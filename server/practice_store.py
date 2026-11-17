"""User-owned project files, revisions, milestones and execution records."""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import secrets
import sqlite3
import threading

from server.practice_contract import file_digest, validate_files


def now():
    return datetime.now(timezone.utc).isoformat()


class Conflict(ValueError):
    pass


class PracticeStore:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.executescript('''
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS workspaces (
                user_id INTEGER, project TEXT, files TEXT, folders TEXT, revision INTEGER,
                completed TEXT, chat TEXT, updated TEXT, PRIMARY KEY(user_id, project));
            CREATE TABLE IF NOT EXISTS snapshots (
                id INTEGER PRIMARY KEY, user_id INTEGER, project TEXT, revision INTEGER,
                files TEXT, folders TEXT, created TEXT);
            CREATE TABLE IF NOT EXISTS runs (
                id TEXT PRIMARY KEY, user_id INTEGER, project TEXT, revision INTEGER,
                digest TEXT, action TEXT, step INTEGER, remote_id TEXT, result TEXT, created TEXT);
            CREATE INDEX IF NOT EXISTS practice_runs_owner ON runs(user_id, project, created);
        ''')
        self.db.commit()

    def workspace(self, user: int, project: dict):
        with self.lock, self.db:
            return self._workspace(user, project)

    def _workspace(self, user, project):
        # Caller owns the lock and transaction; do not commit nested writes.
        self.db.execute('INSERT OR IGNORE INTO workspaces VALUES (?,?,?,?,?,?,?,?)',
                        (user, project['id'], json.dumps(project['files']), '[]', 0, '{}', '[]', now()))
        row = dict(self.db.execute('SELECT * FROM workspaces WHERE user_id=? AND project=?', (user, project['id'])).fetchone())
        for key in ('files', 'folders', 'completed', 'chat'):
            row[key] = json.loads(row[key])
        row.pop('user_id')
        return row

    def save(self, user, project, files, folders, revision):
        validate_files(files, folders)
        with self.lock, self.db:
            self.db.execute('BEGIN IMMEDIATE')
            workspace = self._workspace(user, project)
            if revision != workspace['revision']:
                raise Conflict('Проект изменён в другой вкладке. Скачайте свой черновик и перезагрузите проект.')
            if files == workspace['files'] and sorted(folders) == sorted(workspace['folders']):
                return workspace
            self.db.execute('INSERT INTO snapshots(user_id,project,revision,files,folders,created) VALUES (?,?,?,?,?,?)',
                            (user, project['id'], revision, json.dumps(workspace['files']), json.dumps(workspace['folders']), now()))
            self.db.execute('DELETE FROM snapshots WHERE user_id=? AND project=? AND id NOT IN '
                            '(SELECT id FROM snapshots WHERE user_id=? AND project=? ORDER BY id DESC LIMIT 10)',
                            (user, project['id'], user, project['id']))
            self.db.execute('UPDATE workspaces SET files=?,folders=?,revision=?,updated=? WHERE user_id=? AND project=?',
                            (json.dumps(files), json.dumps(sorted(set(folders))), revision + 1, now(), user, project['id']))
            return self._workspace(user, project)

    def history(self, user, project):
        with self.lock:
            return [dict(r) for r in self.db.execute('SELECT id, revision, created FROM snapshots WHERE user_id=? AND project=? ORDER BY id DESC', (user, project))]

    def restore(self, user, project, snapshot, revision):
        with self.lock:
            row = self.db.execute('SELECT * FROM snapshots WHERE id=? AND user_id=? AND project=?', (snapshot, user, project['id'])).fetchone()
            if not row:
                raise KeyError('Версия не найдена')
            return self.save(user, project, json.loads(row['files']), json.loads(row['folders']), revision)

    def progress(self, user):
        with self.lock:
            return {r['project']: dict(completed=len(json.loads(r['completed'])), revision=r['revision'], updated=r['updated'])
                    for r in self.db.execute('SELECT * FROM workspaces WHERE user_id=?', (user,))}

    def new_run(self, user, project, action, step, revision):
        with self.lock, self.db:
            self.db.execute('BEGIN IMMEDIATE')
            workspace = self._workspace(user, project)
            if workspace['revision'] != revision:
                raise Conflict('Сохраните текущие файлы перед запуском')
            for r in self.db.execute('SELECT result,created FROM runs WHERE user_id=? ORDER BY created DESC LIMIT 8', (user,)):
                if json.loads(r['result'])['status'] in ('queued', 'running'):
                    elapsed = (datetime.now(timezone.utc) - datetime.fromisoformat(r['created'])).total_seconds()
                    if elapsed < 300:
                        raise Conflict('Предыдущий запуск ещё выполняется. Остановите его или дождитесь результата.')
            run = secrets.token_hex(16)
            self.db.execute('INSERT INTO runs VALUES (?,?,?,?,?,?,?,?,?,?)',
                            (run, user, project['id'], revision, file_digest(workspace['files']), action, step,
                             '', json.dumps({'status': 'queued', 'output': ''}), now()))
            # Keep recent results; artifacts can be sizeable.
            self.db.execute('DELETE FROM runs WHERE user_id=? AND project=? AND id NOT IN '
                            '(SELECT id FROM runs WHERE user_id=? AND project=? ORDER BY created DESC LIMIT 12)',
                            (user, project['id'], user, project['id']))
            return self.run(user, run), workspace

    def run(self, user, run):
        with self.lock:
            row = self.db.execute('SELECT * FROM runs WHERE user_id=? AND id=?', (user, run)).fetchone()
            if row is None:
                raise KeyError('Запуск не найден')
            data = dict(row)
            data['result'] = json.loads(data['result'])
            return data

    def update_run(self, user, run, result=None, remote_id=None):
        with self.lock, self.db:
            if result is not None:
                self.db.execute('UPDATE runs SET result=? WHERE id=? AND user_id=?', (json.dumps(result), run, user))
            if remote_id is not None:
                self.db.execute('UPDATE runs SET remote_id=? WHERE id=? AND user_id=?', (remote_id, run, user))
            return self.run(user, run)

    def recent_run(self, user, project):
        with self.lock:
            row = self.db.execute('SELECT id FROM runs WHERE user_id=? AND project=? ORDER BY created DESC LIMIT 1', (user, project)).fetchone()
            return self.run(user, row['id']) if row else None

    def complete(self, user, project, run_id, explanation):
        with self.lock, self.db:
            self.db.execute('BEGIN IMMEDIATE')
            workspace = self._workspace(user, project)
            run = self.run(user, run_id)
            result = run['result']
            if (run['project'] != project['id'] or run['action'] != 'test' or not result.get('passed')
                    or result.get('status') != 'succeeded' or run['revision'] != workspace['revision']
                    or run['digest'] != file_digest(workspace['files'])):
                raise Conflict('Сначала успешно проверьте текущую версию проекта')
            step = run['step']
            if any(str(i) not in workspace['completed'] for i in range(step)):
                raise Conflict('Сначала завершите предыдущие этапы')
            workspace['completed'][str(step)] = {'revision': workspace['revision'], 'explanation': explanation, 'at': now()}
            self.db.execute('UPDATE workspaces SET completed=?,updated=? WHERE user_id=? AND project=?',
                            (json.dumps(workspace['completed']), now(), user, project['id']))
            return self._workspace(user, project)

    def chat(self, user, project, messages):
        with self.lock, self.db:
            self.db.execute('BEGIN IMMEDIATE')
            workspace = self._workspace(user, project)
            history = (workspace['chat'] + messages)[-60:]
            self.db.execute('UPDATE workspaces SET chat=? WHERE user_id=? AND project=?', (json.dumps(history), user, project['id']))
            return history
