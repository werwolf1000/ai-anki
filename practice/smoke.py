"""Check the real Docker worker and authored examples without touching app data.

Run after preparing images: python3 practice/smoke.py
Uses a temporary worker, random loopback port and disposable authentication key.
"""
from __future__ import annotations

import base64
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from server.practice_projects import catalog


def docker(*args, **kwargs):
    return subprocess.check_output(['docker', *args], text=True, **kwargs).strip()


def main():
    name = 'ai-anki-practice-smoke-' + secrets.token_hex(5)
    token = secrets.token_hex(32)
    env = dict(os.environ, AI_ANKI_PRACTICE_TOKEN=token)
    sock = os.environ.get('AI_ANKI_DOCKER_SOCKET', '/var/run/docker.sock')
    try:
        docker('run', '--rm', '-d', '--name', name, '-p', '127.0.0.1::8091',
               '-e', 'AI_ANKI_PRACTICE_TOKEN', '-v', sock + ':/var/run/docker.sock',
               'ai-anki-practice-worker:1', env=env)
        address = docker('port', name, '8091/tcp').splitlines()[0]
        base = 'http://' + address

        def request(method, path, body=None, authenticated=True):
            headers = {'Content-Type': 'application/json'}
            if authenticated:
                headers['Authorization'] = 'Bearer ' + token
            payload = json.dumps(body).encode() if body is not None else None
            with urlopen(Request(base + path, data=payload, headers=headers, method=method), timeout=20) as response:
                return json.load(response)

        deadline = time.monotonic() + 30
        while True:
            try:
                assert request('GET', '/health')['ok']
                break
            except (URLError, ConnectionError):
                if time.monotonic() >= deadline:
                    raise
                time.sleep(.5)
        try:
            request('GET', '/health', authenticated=False)
        except HTTPError as exc:
            assert exc.code == 401
        else:
            raise AssertionError('Worker accepted an unauthenticated request')

        def wait(id):
            deadline = time.monotonic() + 230
            while time.monotonic() < deadline:
                result = request('GET', '/jobs/' + id)
                if result['status'] not in ('queued', 'running'):
                    return result
                time.sleep(.25)
            request('DELETE', '/jobs/' + id)
            raise TimeoutError('Worker did not finish in time')

        for project in catalog().values():
            spec = {key: project[key] for key in ('runtime', 'checks', 'entrypoint')}
            spec.update(files=project['files'] | project['solution'], folders=[], step=len(project['steps']) - 1)
            for action in ('test', 'run'):
                result = wait(request('POST', '/jobs', dict(spec, action=action))['id'])
                assert result['status'] == 'succeeded', (project['id'], action, result)
                if action == 'test':
                    assert result['passed'], (project['id'], result)
                if action == 'run' and project['preview']:
                    html = next(a for a in result['artifacts'] if a['name'] == 'preview.html')
                    assert b'<html' in base64.b64decode(html['data']).lower()
                if action == 'run' and project['id'] == 'python-neural':
                    artifacts = {a['name']: a for a in result['artifacts']}
                    assert 'model.pt' in artifacts
                    metrics = json.loads(base64.b64decode(artifacts['metrics.json']['data']))
                    assert metrics['accuracy'] >= .75, metrics
            print(project['id'] + ': final checks, execution and artifacts OK', flush=True)

        spec = dict(runtime='python', files={'main.py': 'import time\ntime.sleep(300)\n'},
                    folders=[], checks='', entrypoint='main.py', action='run', step=0)
        id = request('POST', '/jobs', spec)['id']
        deadline = time.monotonic() + 20
        while request('GET', '/jobs/' + id)['status'] == 'queued':
            if time.monotonic() >= deadline:
                raise TimeoutError('Cancellation fixture did not start')
            time.sleep(.2)
        assert request('DELETE', '/jobs/' + id)['status'] == 'cancelled'
        assert wait(id)['status'] == 'cancelled'
        print('Worker authentication and cancellation OK', flush=True)
    finally:
        subprocess.run(['docker', 'rm', '-f', name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)


if __name__ == '__main__':
    main()
