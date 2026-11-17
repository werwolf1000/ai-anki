import io
import json
from pathlib import Path
import tarfile
from tempfile import TemporaryDirectory
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
import zipfile

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from server.practice import build_router, parse_reply
from server.practice_contract import validate_files
from server.practice_projects import catalog
from server.practice_store import Conflict, PracticeStore
from server.practice_worker import archive_for, create_app, DockerExecutor, Job, JobIn


class FakeWorker:
    configured = True

    def __init__(self):
        self.jobs = {}
        self.payloads = []

    def request(self, method, path, body=None):
        if method == 'POST':
            id = str(len(self.jobs) + 1)
            self.payloads.append(body)
            self.jobs[id] = {'status': 'succeeded', 'passed': body['action'] == 'test', 'output': 'Checks passed', 'artifacts': []}
            return {'id': id}
        id = path.split('/')[-1]
        if id not in self.jobs:
            raise HTTPException(410, 'Worker restarted')
        if method == 'DELETE':
            self.jobs[id] = {'status': 'cancelled', 'passed': False, 'output': ''}
        return self.jobs[id]


class PracticeApiTest(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.ctx = SimpleNamespace(user=SimpleNamespace(id=1))
        self.llm = Mock()
        self.llm.stream.return_value = iter([json.dumps({'message': 'Начните с проверки пустого имени.', 'patches': []})])
        self.services = SimpleNamespace(data_dir=Path(self.temp.name),
            knowledge=SimpleNamespace(fts_search=lambda *a, **k: [], get_chunks=lambda *a: []),
            check_client=lambda ctx: self.llm)
        self.worker = FakeWorker()
        router = build_router(self.services, lambda: self.ctx, self.worker)
        self.store = router.practice_store
        self.addCleanup(self.store.db.close)
        app = FastAPI(); app.include_router(router)
        self.client = TestClient(app)

    def workspace(self, project='python-tasks'):
        return self.client.get('/api/practice/' + project).json()['workspace']

    def save(self, workspace, project='python-tasks'):
        return self.client.put('/api/practice/' + project, json={k: workspace[k] for k in ('files', 'folders', 'revision')})

    def perform_run(self, workspace, step=0, project='python-tasks', action='test'):
        response = self.client.post('/api/practice/' + project + '/runs', json={'action': action, 'step': step, 'revision': workspace['revision']})
        self.assertEqual(response.status_code, 200, response.text)
        return self.client.get('/api/practice/runs/' + response.json()['id']).json()

    def test_catalog_and_workspace_do_not_leak_solutions_or_checks(self):
        data = self.client.get('/api/practice').json()
        self.assertEqual(len(data['projects']), 8)
        for project in data['projects']:
            self.assertNotIn('solution', project)
            self.assertNotIn('checks', project)
        detail = self.client.get('/api/practice/php-cart').json()
        self.assertIn('src/Cart.php', detail['workspace']['files'])
        self.assertNotIn('solution', detail['project'])

    def test_save_conflict_and_user_isolation(self):
        ws = self.workspace(); ws['files']['notes.txt'] = 'private'
        saved = self.save(ws).json()
        self.assertEqual(saved['revision'], 1)
        self.assertEqual(self.save(ws).status_code, 409)
        self.ctx.user.id = 2
        self.assertNotIn('notes.txt', self.workspace()['files'])
        self.assertEqual(self.client.get('/api/practice/python-tasks/history').json()['snapshots'], [])

    def test_concurrent_connections_cannot_overwrite_a_revision(self):
        self.workspace()
        other = PracticeStore(Path(self.temp.name) / 'practice.db')
        self.addCleanup(other.db.close)
        barrier, results = threading.Barrier(2), []

        def save(store, value):
            barrier.wait()
            try:
                store.save(1, catalog()['python-tasks'], {'main.py': value}, [], 0)
                results.append('saved')
            except Conflict:
                results.append('conflict')

        threads = [threading.Thread(target=save, args=(store, value))
                   for store, value in ((self.store, 'one'), (other, 'two'))]
        for thread in threads: thread.start()
        for thread in threads: thread.join(timeout=5)
        self.assertCountEqual(results, ['saved', 'conflict'])
        self.assertEqual(self.workspace()['revision'], 1)
        self.assertEqual(len(self.store.history(1, 'python-tasks')), 1)

    def test_rejects_unsafe_paths_sizes_and_file_directory_collisions(self):
        for name in ('../secret', '/absolute', 'C:/windows', 'src\\file.py', '.checks/check.py', 'x/../../y', 'a//b'):
            with self.subTest(name=name):
                ws = self.workspace(); ws['files'][name] = 'bad'
                self.assertEqual(self.save(ws).status_code, 422)
        ws = self.workspace(); ws['files']['main.py/child.py'] = 'bad'
        self.assertEqual(self.save(ws).status_code, 422)
        ws = self.workspace(); ws['files']['large.txt'] = 'x' * 512001
        self.assertEqual(self.save(ws).status_code, 422)
        self.assertEqual(self.workspace()['revision'], 0)

    def test_snapshots_restore_and_zip_export(self):
        before = self.workspace(); ws = self.workspace()
        ws['files']['src/new.py'] = 'print(42)'; ws['folders'] = ['empty']
        saved = self.save(ws).json()
        history = self.client.get('/api/practice/python-tasks/history').json()['snapshots']
        self.assertEqual(len(history), 1)
        archive = zipfile.ZipFile(io.BytesIO(self.client.get('/api/practice/python-tasks/export').content))
        self.assertEqual(archive.read('src/new.py'), b'print(42)')
        self.assertIn('empty/', archive.namelist())
        restored = self.client.post('/api/practice/python-tasks/restore', json={'snapshot': history[0]['id'], 'revision': saved['revision']})
        self.assertEqual(restored.json()['files'], before['files'])
        self.ctx.user.id = 2
        response = self.client.post('/api/practice/python-tasks/restore', json={'snapshot': history[0]['id'], 'revision': 0})
        self.assertEqual(response.status_code, 404)

    def test_stage_requires_current_successful_tests_and_explanation(self):
        ws = self.workspace()
        run = self.perform_run(ws)
        endpoint = '/api/practice/python-tasks/complete'
        explanation = 'Я проверяю название и создаю новый список без изменения исходного.'
        self.assertEqual(self.client.post(endpoint, json={'run_id': run['id'], 'explanation': 'ok'}).status_code, 422)
        ws['files']['notes.txt'] = 'change'
        ws = self.save(ws).json()
        self.assertEqual(self.client.post(endpoint, json={'run_id': run['id'], 'explanation': explanation}).status_code, 409)
        run = self.perform_run(ws)
        response = self.client.post(endpoint, json={'run_id': run['id'], 'explanation': explanation})
        self.assertEqual(response.status_code, 200)
        self.assertIn('0', response.json()['completed'])
        self.assertEqual(self.client.post('/api/practice/python-tasks/runs', json={'action':'test','step':2,'revision':ws['revision']}).status_code, 422)
        self.ctx.user.id = 2
        self.assertEqual(self.client.get('/api/practice/runs/' + run['id']).status_code, 404)
        self.assertEqual(self.client.delete('/api/practice/runs/' + run['id']).status_code, 404)

    def test_normal_run_cannot_complete_stage_and_cannot_cross_projects(self):
        run = self.perform_run(self.workspace(), action='run')
        body = {'run_id':run['id'], 'explanation':'Объяснение решения достаточно длинное для проверки.'}
        self.assertEqual(self.client.post('/api/practice/python-tasks/complete', json=body).status_code, 409)
        run = self.perform_run(self.workspace())
        body['run_id'] = run['id']
        self.workspace('php-cart')
        self.assertEqual(self.client.post('/api/practice/php-cart/complete', json=body).status_code, 409)

    def test_runner_payload_uses_server_checks_and_duplicate_run_is_rejected(self):
        ws = self.workspace()
        response = self.client.post('/api/practice/python-tasks/runs', json={'action':'test','step':0,'revision':0})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.worker.payloads[-1]['checks'], catalog()['python-tasks']['checks'])
        self.assertEqual(self.client.post('/api/practice/php-cart/runs', json={'action':'run','step':0,'revision':0}).status_code, 409)
        cancelled = self.client.delete('/api/practice/runs/' + response.json()['id'])
        self.assertEqual(cancelled.json()['result']['status'], 'cancelled')

    def test_disabled_or_restarted_worker_has_actionable_state(self):
        self.worker.configured = False
        self.assertEqual(self.client.post('/api/practice/python-tasks/runs', json={'action':'run','step':0,'revision':0}).status_code, 503)
        self.worker.configured = True
        response = self.client.post('/api/practice/python-tasks/runs', json={'action':'run','step':0,'revision':0})
        self.worker.jobs.clear()
        run = self.client.get('/api/practice/runs/' + response.json()['id'])
        self.assertEqual(run.json()['result']['status'], 'failed')

    def test_mentor_receives_current_files_and_returns_reviewable_patches(self):
        ws = self.workspace(); ws['files']['notes.txt'] = 'MY_CURRENT_CODE'; ws = self.save(ws).json()
        self.llm.stream.return_value = iter([json.dumps({'message':'Предлагаю уточнить комментарий.', 'patches':[{'path':'notes.txt','content':'New comment'}]})])
        response = self.client.post('/api/practice/python-tasks/mentor', json={'message':'Помоги начать', 'step':0, 'revision':ws['revision']})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()['reply']['revision'], ws['revision'])
        self.assertEqual(self.workspace()['files']['notes.txt'], 'MY_CURRENT_CODE')
        prompt = self.llm.stream.call_args.args[0]
        self.assertIn('MY_CURRENT_CODE', prompt[1]['content'])
        self.assertNotIn('"reference"', prompt[1]['content'])
        self.assertEqual(len(self.workspace()['chat']), 2)
        self.assertEqual(self.client.post('/api/practice/python-tasks/mentor', json={'message':'old','step':0,'revision':0}).status_code, 409)
        with self.assertRaises(ValueError):
            parse_reply(json.dumps({'message':'bad','patches':[{'path':'../secret','content':'x'}]}))


class PracticeWorkerTest(unittest.TestCase):
    def spec(self):
        p = catalog()['python-tasks']
        return JobIn(runtime=p['runtime'], files=p['files'], folders=['src/empty'], checks=p['checks'], entrypoint=p['entrypoint'], action='test', step=0)

    def test_container_has_resource_and_privilege_limits(self):
        job = Job('abc123', self.spec())
        args = DockerExecutor().run_command(job)
        for option, value in (('--network','none'),('--user','10001:10001'),('--cap-drop','ALL'),('--pids-limit','64')):
            self.assertEqual(args[args.index(option)+1], value)
        self.assertIn('--read-only', args)
        self.assertIn('--memory', args)
        self.assertIn('--cpus', args)
        self.assertNotIn('--privileged', args)
        self.assertNotIn('-v', args)
        self.assertNotIn('/var/run/docker.sock', ' '.join(args))

    def test_archives_keep_checks_outside_student_workspace(self):
        spec = self.spec(); spec.validate_job()
        with tarfile.open(fileobj=io.BytesIO(archive_for(spec))) as archive:
            self.assertIn('src/empty', archive.getnames())
            self.assertNotIn('check.py', archive.getnames())
            self.assertTrue(all(not p.startswith('/') and '..' not in p.split('/') for p in archive.getnames()))
            self.assertEqual(archive.getmember('main.py').uid, 10001)
        with tarfile.open(fileobj=io.BytesIO(archive_for(spec, checks=True))) as archive:
            self.assertEqual(archive.getnames(), ['check.py'])
            self.assertEqual(archive.getmember('check.py').uid, 0)

    def execute_with_output(self, output, returncode=0):
        job = Job('test-output', self.spec())
        process = Mock(stdout=io.BytesIO(output), returncode=returncode)
        process.poll.return_value = returncode
        executor = DockerExecutor()
        executor.command = Mock(return_value=b'[]')
        executor.stop = Mock()
        with patch('server.practice_worker.subprocess.Popen', return_value=process):
            executor.execute(job)
        executor.stop.assert_called_once_with(job)
        return job, executor

    def test_success_requires_exit_code_and_expected_stage_marker(self):
        job, executor = self.execute_with_output(b'AI_ANKI_CHECK_OK:0\n')
        self.assertTrue(job.result['passed'])
        uploads = [c.args for c in executor.command.call_args_list if c.args[0] == 'exec' and '-i' in c.args]
        self.assertEqual([c[3] for c in uploads], ['10001:10001', '0:0'])
        for args, destination in zip(uploads, ('/workspace', '/checks')):
            self.assertIn('-I', args)
            self.assertIn("filter='data'", args[-1])
            self.assertIn(repr(destination), args[-1])
        self.assertFalse(any(c.args[0] == 'cp' for c in executor.command.call_args_list))
        for output, code in ((b'No checks executed', 0), (b'AI_ANKI_CHECK_OK:1\n', 0), (b'AI_ANKI_CHECK_OK:0\n', 1)):
            job, _ = self.execute_with_output(output, code)
            self.assertFalse(job.result['passed'])

    def test_output_limit_stops_job_and_preserves_bounded_output(self):
        job, _ = self.execute_with_output(b'x' * 70000)
        self.assertEqual(job.result['status'], 'failed')
        self.assertLess(len(job.result['output']), 66000)

    def test_timeout_removes_container_and_kills_docker_exec(self):
        job = Job('test-timeout', self.spec())
        process = Mock(stdout=io.BytesIO(b''))
        process.poll.return_value = None
        executor = DockerExecutor()
        executor.command = Mock(return_value=b'')
        executor.stop = Mock()
        with patch('server.practice_worker.subprocess.Popen', return_value=process), patch('server.practice_worker.time.monotonic', side_effect=[0, 61]):
            executor.execute(job)
        self.assertEqual(job.result['status'], 'failed')
        self.assertIn('Превышено время', job.result['output'])
        executor.stop.assert_called_once_with(job)
        process.kill.assert_called_once()

    def test_worker_authentication_validation_and_cancellation(self):
        started, released = threading.Event(), threading.Event()
        class Executor:
            def execute(self, job):
                job.result['status'] = 'running'; started.set(); released.wait(5)
            def stop(self, job): released.set()
        app = create_app(Executor(), token='t'*32)
        client = TestClient(app)
        spec = self.spec().model_dump()
        self.assertEqual(client.post('/jobs', json=spec).status_code, 401)
        headers = {'Authorization':'Bearer ' + 't'*32}
        bad = dict(spec, runtime='python;rm -rf /')
        self.assertEqual(client.post('/jobs', json=bad, headers=headers).status_code, 422)
        response = client.post('/jobs', json=spec, headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(started.wait(2))
        id = response.json()['id']
        self.assertEqual(client.get('/jobs/'+id).status_code, 401)
        self.assertEqual(client.delete('/jobs/'+id, headers=headers).json()['status'], 'cancelled')
        self.assertTrue(released.is_set())


if __name__ == '__main__':
    unittest.main()
