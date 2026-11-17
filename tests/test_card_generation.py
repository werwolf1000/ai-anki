import json
import hashlib
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from app.registry import DeckRegistry
from server.book_decks import BookDecks, CardJob, GenerateIn, build_router
from server.card_targets import card_targets
from server.syllabus import Chapter, Syllabus
from fastapi import FastAPI
from fastapi.testclient import TestClient


class CardGenerationTest(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        reg = DeckRegistry(root / 'registry.json', root / 'builtin', root / 'decks')
        reg.load()
        self.services = SimpleNamespace(data_dir=root, registry=reg, _deck_cache={}, _contexts={})
        self.books = self.services.books = BookDecks(self.services)
        self.sy = Syllabus('example', 'Профессия', '', [Chapter('Глава', ['Урок'])], kind='code', lang='python', track='python')
        self.normal = Syllabus('ordinary', 'Обычный учебник', '', [Chapter('Глава', ['Урок'])], kind='code', lang='python')
        self.books.sync_meta(self.sy)
        self.books._write(self.books.paths(self.sy)[0], {'cards': []})
        self.n = 0

    def generate(self, sy, lesson, need, live, existing):
        # Deliberately return less than requested, like a real partial model reply.
        out = []
        for _ in range(min(2, need)):
            self.n += 1
            token = ''.join(chr(97 + b % 26) for b in hashlib.sha256(str(self.n).encode()).digest()[:12])
            out.append({'id':str(self.n), 'question':f'Объясните понятие {token}',
                        'reference': f'Точный эталон решения {self.n}', 'topic':lesson,
                        'card_type':'live_code' if live else 'text'})
        return out

    def run_job(self, body=None, generator=None):
        body = body or GenerateIn(book=self.sy.id)
        self.books._generation_request = body
        self.books.job = CardJob(running=True, status='running', total=1)
        with patch('server.book_decks.all_syllabi', return_value=[self.sy]), patch('server.book_decks.get_syllabus', return_value=self.sy), patch.object(self.books, '_generate', side_effect=generator or self.generate):
            self.books._run([(self.sy.id, 'Урок')], body)
        return self.books.job

    def test_profession_minimum_cannot_be_lowered_by_old_clients(self):
        self.assertEqual(card_targets(self.sy), {'qa':20, 'live':10})
        self.assertEqual(card_targets(self.sy, 8, 3), {'qa':20, 'live':10})
        self.assertEqual(card_targets(self.normal), {'qa':8, 'live':3})
        self.assertEqual(card_targets(self.normal, 1, 0), {'qa':1, 'live':0})
        self.sy.kind = 'theory'; self.sy.lang = 'markdown'
        self.assertEqual(card_targets(self.sy), {'qa':20, 'live':10})

    def test_partial_batches_reach_both_minima_and_preserve_existing_cards(self):
        original = {'id':'existing', 'question':'Каким образом работает сохранение?', 'reference':'Исходный ответ', 'topic':'Урок'}
        self.books._write(self.books.paths(self.sy)[0], {'cards':[original]})
        job = self.run_job(GenerateIn(qa_target=1, live_target=1))
        self.assertEqual(self.books.lesson_counts(self.sy)['Урок'], {'qa':20, 'live':10})
        self.assertEqual((job.status, job.remaining_lessons), ('completed', 0))
        self.assertEqual(job.added_qa, 19)
        self.assertEqual(self.books._read(self.books.paths(self.sy)[0])['cards'][0], original)
        before = self.n
        self.run_job()
        self.assertEqual(self.n, before, 'Already full lessons must not call the model')

    def test_empty_generation_is_incomplete_and_bounded(self):
        job = self.run_job(generator=lambda *args: [])
        self.assertEqual(job.status, 'incomplete')
        self.assertEqual((job.remaining_qa, job.remaining_live), (20, 10))
        self.assertEqual(job.failed, 1)
        self.assertIn('Не завершено', job.log[-1])

    def test_append_deduplicates_same_batch_and_respects_retirement(self):
        path = self.books.paths(self.sy)[0]
        self.books._write(path, {'cards':[], 'retired_ids':['retired']})
        c = {'id':'first', 'question':'Как работает синхронизация потоков?', 'reference':'Ответ', 'topic':'Урок'}
        added = self.books._append(self.sy, False, [c, dict(c, id='second'), dict(c, id='retired')])
        self.assertEqual(added, 1)

    def test_resume_only_interrupted_jobs_and_stop_persists(self):
        body = GenerateIn(professions_only=True, workers=4)
        self.books._generation_request = body
        self.books.job = CardJob(running=True, status='running')
        self.books._checkpoint()
        with patch.object(self.books, 'start_generation') as start:
            self.books.resume_generation()
            self.assertEqual(start.call_args.args[0], body)
        self.books.stop_generation()
        with patch.object(self.books, 'start_generation') as start:
            self.books.resume_generation()
            start.assert_not_called()

    def test_profession_filter_and_api_targets(self):
        with patch('server.book_decks.all_syllabi', return_value=[self.sy, self.normal]), patch('server.book_decks.get_syllabus', return_value=self.sy):
            report = self.books.coverage(GenerateIn(professions_only=True))
            self.assertEqual(report['items'], [(self.sy.id, 'Урок')])
            app = FastAPI(); app.include_router(build_router(self.services, lambda: SimpleNamespace(user=SimpleNamespace(is_admin=True))))
            client = TestClient(app)
            self.assertEqual(client.get('/api/books/example').json()['targets'], {'qa':20, 'live':10})
            self.assertEqual(client.get('/api/books').json()['books'][0]['thin'], 1)
            for body in ({'workers':0}, {'workers':5}, {'qa_target':-1}, {'live_target':1000}):
                self.assertEqual(client.post('/api/books/generate', json=body).status_code, 422)

    def test_generate_uses_actual_language_and_rejects_broken_python(self):
        replies = [
            {'task':'Напишите безопасный SQL-запрос поиска пользователя', 'solution':'SELECT id FROM users WHERE email = :email;', 'language':'sql'},
            {'task':'Реализуйте функцию с обработкой пустого списка', 'solution':'def invalid(:\n    pass', 'language':'python'},
            {'task':'Некорректный ответ без строкового эталона', 'solution':['not', 'a', 'solution']},
        ]
        self.services.textbook_llm = lambda: SimpleNamespace(stream=lambda *a, **k: iter([json.dumps(replies)]))
        cards = self.books._generate(self.sy, 'Урок', 2, True, [])
        self.assertEqual(len(cards), 1)
        self.assertEqual(cards[0]['language'], 'sql')
        self.assertTrue(cards[0]['id'].startswith('gen-'))

    def test_parallel_lessons_preserve_each_others_cards(self):
        self.sy.chapters[0].lessons = ['Первый урок', 'Второй урок']
        barrier = threading.Barrier(2)
        entered = set()
        guard = threading.Lock()

        def generate(sy, lesson, need, live, existing):
            if lesson not in entered:
                entered.add(lesson)
                barrier.wait(timeout=5)
            with guard:
                return self.generate(sy, lesson, need, live, existing)

        body = GenerateIn(professions_only=True, workers=2)
        self.books._generation_request = body
        self.books.job = CardJob(running=True, status='running', total=2)
        with patch('server.book_decks.all_syllabi', return_value=[self.sy]), patch('server.book_decks.get_syllabus', return_value=self.sy), patch.object(self.books, '_generate', side_effect=generate):
            self.books._run([(self.sy.id, lesson) for lesson in self.sy.lesson_titles()], body)
            self.assertEqual(self.books.coverage(body)['remaining_lessons'], 0)
        self.assertEqual(self.books.job.status, 'completed')
        self.assertEqual(self.books.job.added_qa, 40)
        self.assertEqual(self.books.job.added_live, 20)
        for count in self.books.lesson_counts(self.sy).values():
            self.assertEqual(count, {'qa':20, 'live':10})

    def test_full_resume_closes_checkpoint_without_model_calls(self):
        self.run_job()
        with patch('server.book_decks.all_syllabi', return_value=[self.sy]), patch('server.book_decks.get_syllabus', return_value=self.sy), patch.object(self.books, '_generate') as generate:
            self.books.job.status = 'running'
            self.books._checkpoint()
            self.books.resume_generation()
            generate.assert_not_called()
        saved = self.books._read(self.books.generation_path)
        self.assertEqual(saved['job']['status'], 'completed')
        self.assertFalse(saved['job']['running'])

    def test_desktop_bridge_bulk_job_uses_one_worker(self):
        self.services.config = {'llm_textbook':'bridge:123'}
        with patch('server.book_decks.ThreadPoolExecutor', wraps=ThreadPoolExecutor) as executor:
            job = self.run_job(GenerateIn(professions_only=True, workers=4))
        self.assertEqual(executor.call_args.kwargs['max_workers'], 1)
        self.assertEqual(job.status, 'completed')
        self.assertEqual(self.books.lesson_counts(self.sy)['Урок'], {'qa':20, 'live':10})

    def test_card_generation_uses_selected_desktop_bridge(self):
        from server.llm import BridgeHub, make_client
        hub = BridgeHub()
        user_id = 123
        hub.poll(user_id, {'model':'local-test-model'}, wait=0)
        self.services.config = {'llm_textbook':f'bridge:{user_id}'}
        self.services.textbook_llm = lambda: make_client(self.services.config, self.services.config['llm_textbook'], hub=hub)
        reply = [{'question':'Как локальная модель возвращает карточки на сервер?',
                  'reference':'Приложение передаёт ответ через мост. Сервер проверяет карточки и сохраняет их в колоду.'}]
        with patch('server.llm.requests.post', side_effect=AssertionError('An external provider must not be called')):
            with ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(self.books._generate, self.sy, 'Урок', 1, False, [])
                request = hub.poll(user_id, {'model':'local-test-model'}, wait=2)
                self.assertIsNotNone(request)
                self.assertIn('Урок: Урок', request.payload['messages'][1]['content'])
                self.assertTrue(hub.push(user_id, request.id, {'delta':json.dumps(reply, ensure_ascii=False), 'done':True}))
                cards = future.result(timeout=3)
        self.assertEqual(len(cards), 1)
        self.assertEqual(cards[0]['question'], reply[0]['question'])
        self.assertEqual(cards[0]['topic'], 'Урок')


if __name__ == '__main__':
    unittest.main()
