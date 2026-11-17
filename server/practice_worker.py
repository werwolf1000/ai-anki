"""Separate, authenticated Docker worker. Never execute student code on the API host.

Start with uvicorn server.practice_worker:create_app --factory --port 8091.
Run this service on a dedicated worker/VM; its Docker daemon is privileged.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hmac
import io
import json
import os
import secrets
import subprocess
import tarfile
import threading
import time

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from server.practice_contract import RUNTIMES, validate_files, validate_path


class JobIn(BaseModel):
    runtime: str
    files: dict[str, str]
    folders: list[str] = Field(default_factory=list, max_length=64)
    checks: str = Field(max_length=64000)
    entrypoint: str
    action: str = Field(pattern='^(run|test)$')
    step: int = Field(ge=0, le=30)

    def validate_job(self):
        validate_files(self.files, self.folders)
        if self.runtime not in RUNTIMES:
            raise ValueError('Неизвестное окружение')
        validate_path(self.entrypoint)
        expected = 'main.php' if self.runtime == 'php' else 'main.py'
        if self.entrypoint != expected or self.entrypoint not in self.files:
            raise ValueError(f'Нужен файл {expected}')


IMAGES = {
    'python': 'ai-anki-practice-base:1', 'php': 'ai-anki-practice-base:1',
    'python-data': 'ai-anki-practice-data:1', 'python-ml': 'ai-anki-practice-ml:1',
}


def archive_for(spec: JobIn, checks=False) -> bytes:
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode='w') as archive:
        directories = set()
        for path in ([] if checks else [*spec.files, *[p + '/.keep' for p in spec.folders]]):
            parts = path.split('/')
            directories.update('/'.join(parts[:i]) for i in range(1, len(parts)))
        for path in sorted(directories, key=lambda p: (p.count('/'), p)):
            info = tarfile.TarInfo(path)
            info.type, info.mode = tarfile.DIRTYPE, 0o755
            info.uid = info.gid = 10001
            archive.addfile(info)
        extension = 'php' if spec.runtime == 'php' else 'py'
        files = {'check.' + extension: spec.checks} if checks else spec.files
        for path, content in files.items():
            raw = content.encode('utf-8')
            info = tarfile.TarInfo(path)
            info.size, info.mode = len(raw), 0o644
            info.uid = info.gid = 0 if checks else 10001
            archive.addfile(info, io.BytesIO(raw))
    return output.getvalue()


@dataclass
class Job:
    id: str
    spec: JobIn
    created: float = field(default_factory=time.time)
    cancelled: threading.Event = field(default_factory=threading.Event)
    result: dict = field(default_factory=lambda: {'status': 'queued', 'output': '', 'passed': False, 'artifacts': []})

    @property
    def container(self):
        return 'ai-anki-practice-' + self.id


class DockerExecutor:
    def command(self, *args, input=None, timeout=30):
        process = subprocess.run(['docker', *args], input=input, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, timeout=timeout, check=False)
        if process.returncode:
            raise RuntimeError(process.stderr.decode('utf-8', 'replace')[-3000:] or 'Docker: операция не выполнена')
        return process.stdout

    def run_command(self, job):
        ml = job.spec.runtime == 'python-ml'
        memory = '1536m' if ml else '768m' if job.spec.runtime == 'python-data' else '384m'
        return ['run', '-d', '--rm', '--name', job.container, '--label', 'ai-anki.practice=1',
                '--network', 'none', '--read-only', '--cap-drop', 'ALL',
                '--security-opt', 'no-new-privileges:true', '--pids-limit', '64',
                '--memory', memory, '--memory-swap', memory, '--cpus', '1',
                '--user', '10001:10001', '--workdir', '/workspace',
                '--tmpfs', '/workspace:rw,nosuid,size=64m,uid=10001,gid=10001,mode=0755',
                '--tmpfs', '/checks:rw,nosuid,size=1m,mode=0755',
                '--tmpfs', '/tmp:rw,noexec,nosuid,size=64m,mode=1777',
                '-e', 'HOME=/tmp', '-e', 'MPLCONFIGDIR=/tmp/matplotlib', '-e', 'MPLBACKEND=Agg',
                '-e', 'PYTHONDONTWRITEBYTECODE=1', '-e', 'OMP_NUM_THREADS=1', '-e', 'OPENBLAS_NUM_THREADS=1',
                IMAGES[job.spec.runtime], 'sleep', '300']

    def stop(self, job):
        try:
            self.command('rm', '-f', job.container, timeout=15)
        except (OSError, RuntimeError, subprocess.TimeoutExpired):
            pass

    def execute(self, job):
        process = None
        try:
            if job.cancelled.is_set():
                return
            self.command(*self.run_command(job))
            self.command('cp', '-a', '-', job.container + ':/workspace', input=archive_for(job.spec))
            self.command('cp', '-a', '-', job.container + ':/checks', input=archive_for(job.spec, checks=True))
            if job.cancelled.is_set():
                return
            php = job.spec.runtime == 'php'
            command = ['php', '-d', 'display_errors=stderr'] if php else ['python', '-u']
            command += (['/checks/check.' + ('php' if php else 'py'), str(job.spec.step)]
                        if job.spec.action == 'test' else [job.spec.entrypoint])
            job.result['status'] = 'running'
            process = subprocess.Popen(['docker', 'exec', '-w', '/workspace', '--user', '10001:10001', job.container, *command],
                                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            output, overflow = bytearray(), threading.Event()

            def read_output():
                while True:
                    block = process.stdout.read1(4096)
                    if not block:
                        break
                    room = 65536 - len(output)
                    output.extend(block[:room])
                    job.result['output'] = output.decode('utf-8', 'replace')
                    if len(block) > room:
                        overflow.set()
                        break

            reader = threading.Thread(target=read_output, daemon=True)
            reader.start()
            deadline = time.monotonic() + (180 if job.spec.runtime == 'python-ml' else 60)
            while process.poll() is None:
                if job.cancelled.is_set():
                    raise InterruptedError('Запуск остановлен')
                if overflow.is_set():
                    raise RuntimeError('Вывод превысил 64 КБ. Уменьшите количество сообщений.')
                if time.monotonic() > deadline:
                    raise TimeoutError('Превышено время выполнения')
                time.sleep(0.1)
            reader.join(timeout=2)
            if overflow.is_set():
                raise RuntimeError('Вывод превысил 64 КБ')
            if job.cancelled.is_set():
                raise InterruptedError('Запуск остановлен')
            passed = (job.spec.action == 'test' and process.returncode == 0
                      and f'AI_ANKI_CHECK_OK:{job.spec.step}' in job.result['output'].splitlines())
            job.result.update(exit_code=process.returncode, passed=passed)
            if process.returncode == 0:
                artifacts = self.command('exec', '--user', '10001:10001', job.container,
                                         'python', '-I', '/opt/export_artifacts.py', timeout=10)
                job.result['artifacts'] = json.loads(artifacts)
            job.result['status'] = 'succeeded' if process.returncode == 0 else 'failed'
        except Exception as exc:
            job.result.update(status='cancelled' if job.cancelled.is_set() else 'failed', passed=False,
                              output=job.result['output'] + '\n' + str(exc)[-3000:])
        finally:
            if job.cancelled.is_set():
                job.result.update(status='cancelled', passed=False)
            self.stop(job)
            if process is not None:
                if process.poll() is None:
                    process.kill()
                process.wait(timeout=5)
                process.stdout.close()


def create_app(executor=None, token=None):
    token = token or os.environ.get('AI_ANKI_PRACTICE_TOKEN', '')
    if len(token) < 32:
        raise RuntimeError('AI_ANKI_PRACTICE_TOKEN должен содержать не менее 32 символов')
    executor = executor or DockerExecutor()
    app = FastAPI(title='AI Anki practice worker', docs_url=None, redoc_url=None, openapi_url=None)
    jobs, lock = {}, threading.RLock()
    slots = threading.BoundedSemaphore(max(1, min(4, int(os.environ.get('AI_ANKI_PRACTICE_PARALLEL', '2')))))

    def authorize(authorization: str = Header(default='')):
        if not hmac.compare_digest(authorization, 'Bearer ' + token):
            raise HTTPException(401, 'Требуется ключ сервиса')

    def lookup(id):
        with lock:
            if id not in jobs:
                raise HTTPException(404, 'Запуск истёк или сервис был перезапущен')
            return jobs[id]

    @app.get('/health', dependencies=[Depends(authorize)])
    def health():
        try:
            executor.command('info', '--format', '{{.ServerVersion}}', timeout=5)
        except Exception as exc:
            raise HTTPException(503, 'Docker недоступен') from exc
        return {'ok': True, 'runtimes': sorted(RUNTIMES)}

    @app.post('/jobs', dependencies=[Depends(authorize)])
    def start(body: JobIn):
        try:
            body.validate_job()
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc
        if not slots.acquire(blocking=False):
            raise HTTPException(429, 'Все среды заняты')
        job = Job(secrets.token_hex(16), body)
        with lock:
            for id, old in list(jobs.items()):
                if time.time() - old.created > 3600 and old.result['status'] not in ('queued', 'running'):
                    del jobs[id]
            jobs[job.id] = job

        def run():
            try:
                executor.execute(job)
            finally:
                slots.release()

        threading.Thread(target=run, daemon=True, name='practice-' + job.id[:8]).start()
        return {'id': job.id}

    @app.get('/jobs/{id}', dependencies=[Depends(authorize)])
    def get_job(id: str):
        return dict(lookup(id).result)

    @app.delete('/jobs/{id}', dependencies=[Depends(authorize)])
    def cancel(id: str):
        job = lookup(id)
        if job.result['status'] in ('queued', 'running'):
            job.cancelled.set()
            executor.stop(job)
            job.result.update(status='cancelled', passed=False)
        return dict(job.result)

    return app
