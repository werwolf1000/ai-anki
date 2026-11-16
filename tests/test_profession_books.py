import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.progress import CardProgress, ProgressStore
from app.registry import DeckRegistry
from server.book_decks import BookDecks
from server.lesson_quiz import build_router as quiz_router, validate_questions
from server.syllabus import all_syllabi, get_syllabus, syllabus_for, track_syllabus
from server.tracks import TrackStore, build_router as tracks_router

ROOT = Path(__file__).resolve().parents[1]


class ProfessionBooksTest(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.data = Path(self.tmp.name)
        self.env = patch.dict(os.environ, {"AI_ANKI_SYLLABUS_DIR": str(self.data / "syllabus")})
        self.env.start()
        self.addCleanup(self.env.stop)
        registry = DeckRegistry(self.data / "registry.json", ROOT / "decks", self.data / "decks")
        registry.load()
        self.services = SimpleNamespace(root=ROOT, data_dir=self.data, registry=registry,
                                        _deck_cache={}, _contexts={}, load_deck=registry.load_deck,
                                        pass_score=lambda ctx: 75)
        self.books = self.services.books = BookDecks(self.services)

    def test_every_profession_has_lessons_and_both_decks(self):
        tracks = json.loads((ROOT / "decks/tracks.json").read_text(encoding="utf-8"))["tracks"]
        for track in tracks:
            with self.subTest(track=track["id"]):
                sy = track_syllabus(track["id"])
                self.assertIsNotNone(sy)
                self.assertGreaterEqual(len(sy.lesson_titles()), 30)
                self.books.build(sy)
                source_ids = set()
                for entry in self.books.source_entries(sy):
                    source_ids.update(c.id for c in self.services.load_deck(entry).cards)
                migrated = set()
                for path in self.books.paths(sy):
                    cards = self.books._read(path)["cards"]
                    self.assertTrue(cards)
                    self.assertTrue(all(c["topic"] in sy.lesson_titles() for c in cards))
                    migrated.update(c["id"] for c in cards)
                self.assertEqual(source_ids, migrated)
                self.assertEqual(set(self.books.deck_ids(sy)), {"qa", "live"})
        self.assertEqual(syllabus_for("", "PHP 8+", ["php8-plus.json"]).id, "php")
        self.assertEqual(syllabus_for("", "PHP-разработчик", ["pro-php.json"]).id, "pro_php")

    def test_old_syllabus_override_retains_track(self):
        sy = get_syllabus("ai_artist")
        text = sy.to_text().replace("track: ai-artist\n", "")
        directory = self.data / "syllabus"
        directory.mkdir()
        (directory / "ai_artist.txt").write_text(text, encoding="utf-8")
        self.assertEqual(track_syllabus("ai-artist").id, "ai_artist")

    def test_upgrade_splits_practice_and_preserves_progress_and_retirement(self):
        sy = track_syllabus("ai-artist")
        self.books.build(sy)
        qa_path, live_path = self.books.paths(sy)
        qa, live = self.books._read(qa_path), self.books._read(live_path)
        card = live["cards"][0]
        qa["cards"].extend(live["cards"])
        self.books._write(qa_path, qa)
        self.books._write(live_path, {**live, "cards": []})
        ids = self.books.deck_ids(sy)
        progress = ProgressStore(self.data / "progress.json")
        progress.data[ids["qa"]] = {card["id"]: CardProgress(card["id"], attempts=4, best_score=90)}
        self.books.state.pop("track_books", None)
        with patch("server.book_decks.all_syllabi", return_value=[sy]):
            self.books.ensure_all()
        self.assertTrue(self.books.migrate_progress(progress))
        self.assertEqual(progress.data[ids["live"]][card["id"]].best_score, 90)
        self.assertTrue(all(c["card_type"] != "live_code" for c in self.books._read(qa_path)["cards"]))
        self.books._rewrite_cards(sy, lambda c: None if c["id"] == card["id"] else c)
        self.books.build(sy)
        self.assertNotIn(card["id"], {c["id"] for c in self.books._read(live_path)["cards"]})

    def test_track_progress_and_exam_use_book_cards(self):
        sy = track_syllabus("php")
        self.books.build(sy)
        qa_path, live_path = self.books.paths(sy)
        for path in (qa_path, live_path):
            data = self.books._read(path)
            data["cards"] = data["cards"][:1]
            self.books._write(path, data)
        ctx = SimpleNamespace(user=SimpleNamespace(id=1), lock=threading.RLock(), progress=ProgressStore(self.data / "progress.json"))
        app = FastAPI()
        store = TrackStore(self.data / "tracks.db")
        self.addCleanup(store._db.close)
        with patch("server.tracks.TrackStore", return_value=store):
            app.include_router(tracks_router(self.services, lambda: ctx))
        with TestClient(app) as client:
            detail = client.get("/api/tracks/php").json()
            self.assertEqual(detail["requirements"]["coverage"]["total"], 2)
            self.assertEqual(detail["book"]["id"], sy.id)
            self.assertEqual({d["deck_id"] for d in detail["decks"]}, set(self.books.deck_ids(sy).values()))
            exam = client.post("/api/tracks/php/exam")
            self.assertEqual(exam.status_code, 200)
            self.assertEqual(len(exam.json()["questions"]), 2)

    def test_quiz_validation_and_user_isolation(self):
        questions = [{"question": f"Вопрос {i}", "options": ["а", "б", "в", "г"], "correct": i % 4, "explanation": "Пояснение"} for i in range(5)]
        with self.assertRaises(ValueError):
            validate_questions([{**q, "correct": True} for q in questions])
        self.services.lesson_context = lambda *args: "Материалы урока"
        self.services.textbook_llm = lambda: SimpleNamespace(stream=lambda *args, **kwargs: iter([json.dumps(questions, ensure_ascii=False)]))
        ctx = SimpleNamespace(user=SimpleNamespace(id=1))
        app = FastAPI()
        app.include_router(quiz_router(self.services, lambda: ctx))
        with TestClient(app) as client:
            sy = track_syllabus("php")
            response = client.post(f"/api/books/{sy.id}/quiz", json={"lesson": sy.lesson_titles()[0]})
            self.assertEqual(response.status_code, 200, response.text)
            quiz = response.json()
            self.assertNotIn("correct", quiz["questions"][0])
            url = f"/api/lesson-quizzes/{quiz['id']}/check"
            ctx.user.id = 2
            self.assertEqual(client.post(url, json={"answers": [0, 1, 2, 3, 0]}).status_code, 404)
            ctx.user.id = 1
            self.assertEqual(client.post(url, json={"answers": [0]}).status_code, 422)
            self.assertEqual(client.post(url, json={"answers": [0, 1, 2, 3, 0]}).json()["score"], 5)
            self.assertEqual(client.post(f"/api/books/{sy.id}/quiz", json={"lesson": "Нет такого урока"}).status_code, 404)


if __name__ == "__main__":
    unittest.main()
