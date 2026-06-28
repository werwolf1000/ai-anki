from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from app.deck import Deck


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def _parse_iso(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


class StudyMode(str, Enum):
    DUE = "due"
    NEW = "new"
    WEAK = "weak"
    ALL = "all"


@dataclass
class AnswerRecord:
    at: str
    answer: str
    score: int
    correct: bool
    feedback: str
    is_follow_up: bool = False
    finalized: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AnswerRecord:
        return cls(
            at=data.get("at", ""),
            answer=data.get("answer", ""),
            score=int(data.get("score", 0)),
            correct=bool(data.get("correct", False)),
            feedback=data.get("feedback", ""),
            is_follow_up=bool(data.get("is_follow_up", False)),
            finalized=bool(data.get("finalized", False)),
        )


@dataclass
class CardProgress:
    card_id: str
    attempts: int = 0
    best_score: int = 0
    last_score: int = 0
    mastered: bool = False
    interval_days: float = 0.0
    ease: float = 2.5
    due_at: str = ""
    last_reviewed_at: str = ""
    history: list[AnswerRecord] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CardProgress:
        history = [AnswerRecord.from_dict(h) for h in data.get("history", [])]
        return cls(
            card_id=data.get("card_id", ""),
            attempts=int(data.get("attempts", 0)),
            best_score=int(data.get("best_score", 0)),
            last_score=int(data.get("last_score", 0)),
            mastered=bool(data.get("mastered", False)),
            interval_days=float(data.get("interval_days", 0)),
            ease=float(data.get("ease", 2.5)),
            due_at=data.get("due_at", ""),
            last_reviewed_at=data.get("last_reviewed_at", ""),
            history=history,
        )

    def is_due(self, now: datetime | None = None) -> bool:
        now = now or _now()
        if self.attempts == 0:
            return True
        due = _parse_iso(self.due_at)
        if due is None:
            return True
        return due <= now

    def is_new(self) -> bool:
        return self.attempts == 0

    def days_until_due(self, now: datetime | None = None) -> float:
        now = now or _now()
        due = _parse_iso(self.due_at)
        if due is None:
            return 0.0
        return (due - now).total_seconds() / 86400


def _local_today(now: datetime | None = None):
    if now is None:
        now = _now()
    return now.astimezone().date()


def _record_on_local_day(at: str, day) -> bool:
    ts = _parse_iso(at)
    if ts is None:
        return False
    return ts.astimezone().date() == day


@dataclass
class DeckSummary:
    deck_id: str
    total: int
    mastered: int
    passed_today: int
    due: int
    new: int
    weak: int
    studied: int
    last_reviewed_at: str = ""
    avg_score: float = 0.0


class ProgressStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.data: dict[str, dict[str, CardProgress]] = {}

    def load(self) -> None:
        if not self.path.exists():
            self.data = {}
            return
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        self.data = {}
        for deck_key, cards in raw.items():
            self.data[deck_key] = {
                cid: CardProgress.from_dict(values) if isinstance(values, dict) else CardProgress(card_id=cid)
                for cid, values in cards.items()
            }

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload: dict[str, dict[str, dict[str, Any]]] = {}
        for deck_key, cards in self.data.items():
            payload[deck_key] = {}
            for cid, prog in cards.items():
                d = asdict(prog)
                d["history"] = [asdict(h) for h in prog.history]
                payload[deck_key][cid] = d
        text = json.dumps(payload, ensure_ascii=False, indent=2)
        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(text, encoding="utf-8")
        tmp.replace(self.path)

    def deck_key(self, deck: Deck) -> str:
        return deck.deck_id or deck.name

    def get(self, deck: Deck, card_id: str) -> CardProgress:
        key = self.deck_key(deck)
        deck_map = self.data.setdefault(key, {})
        if card_id not in deck_map:
            deck_map[card_id] = CardProgress(card_id=card_id)
        return deck_map[card_id]

    def record_answer(
        self,
        deck: Deck,
        card_id: str,
        *,
        answer: str,
        score: int,
        correct: bool,
        feedback: str,
        pass_score: int,
        is_follow_up: bool = False,
        finalize: bool = True,
    ) -> CardProgress:
        prog = self.get(deck, card_id)
        now = _now()

        record = AnswerRecord(
            at=_iso(now),
            answer=answer[:4000],
            score=score,
            correct=correct,
            feedback=feedback[:2000],
            is_follow_up=is_follow_up,
            finalized=finalize,
        )
        prog.history.append(record)
        if len(prog.history) > 50:
            prog.history = prog.history[-50:]

        if finalize:
            prog.attempts += 1
            prog.last_score = score
            prog.best_score = max(prog.best_score, score)
            prog.last_reviewed_at = _iso(now)
            passed = score >= pass_score
            self._apply_srs(prog, score, pass_score, now, passed=passed)

        self.data[self.deck_key(deck)][card_id] = prog
        self.save()
        return prog

    @staticmethod
    def _apply_srs(prog: CardProgress, score: int, pass_score: int, now: datetime, *, passed: bool) -> None:
        if passed:
            if prog.interval_days <= 0:
                prog.interval_days = 1.0
            else:
                prog.interval_days = min(180.0, prog.interval_days * prog.ease)
            if score >= 90:
                prog.ease = min(3.0, prog.ease + 0.15)
            elif score >= pass_score:
                prog.ease = min(3.0, prog.ease + 0.05)
            prog.mastered = prog.interval_days >= 7 and prog.best_score >= pass_score
            due = now + timedelta(days=prog.interval_days)
        else:
            prog.interval_days = 0.0
            prog.ease = max(1.3, prog.ease - 0.2)
            prog.mastered = False
            minutes = 10 if score >= pass_score // 2 else 5
            due = now + timedelta(minutes=minutes)

        prog.due_at = _iso(due)

    @staticmethod
    def _passed_today(prog: CardProgress, pass_score: int, day) -> bool:
        for rec in prog.history:
            finalized = rec.finalized or not rec.is_follow_up
            if not finalized:
                continue
            if _record_on_local_day(rec.at, day) and rec.score >= pass_score:
                return True
        return False

    def summary(self, deck: Deck, pass_score: int = 75) -> DeckSummary:
        key = self.deck_key(deck)
        cards_map = self.data.get(key, {})
        mastered = studied = passed_today = 0
        scores: list[int] = []
        last_at = ""
        today = _local_today()

        for card in deck.cards:
            prog = cards_map.get(card.id) or CardProgress(card_id=card.id)
            if prog.attempts > 0:
                studied += 1
                scores.append(prog.best_score)
            if prog.mastered or (prog.interval_days >= 7 and prog.best_score >= pass_score):
                mastered += 1
            if self._passed_today(prog, pass_score, today):
                passed_today += 1
            if prog.last_reviewed_at and prog.last_reviewed_at > last_at:
                last_at = prog.last_reviewed_at

        due = sum(
            1
            for c in deck.cards
            if (p := cards_map.get(c.id) or CardProgress(card_id=c.id)) and (p.is_new() or p.is_due())
        )
        new = sum(
            1 for c in deck.cards if (cards_map.get(c.id) or CardProgress(card_id=c.id)).is_new()
        )
        weak = sum(
            1
            for c in deck.cards
            if (p := cards_map.get(c.id)) and p.attempts > 0 and p.best_score < pass_score
        )

        avg = sum(scores) / len(scores) if scores else 0.0
        return DeckSummary(
            deck_id=key,
            total=len(deck.cards),
            mastered=mastered,
            passed_today=passed_today,
            due=due,
            new=new,
            weak=weak,
            studied=studied,
            last_reviewed_at=last_at,
            avg_score=round(avg, 1),
        )

    def build_queue(
        self,
        deck: Deck,
        mode: StudyMode,
        *,
        pass_score: int = 75,
        limit: int = 50,
    ) -> list:
        now = _now()
        key = self.deck_key(deck)
        cards_map = self.data.get(key, {})

        def prog(card):
            return cards_map.get(card.id) or CardProgress(card_id=card.id)

        candidates: list[tuple[int, float, Any]] = []

        for card in deck.cards:
            p = prog(card)
            if mode == StudyMode.NEW:
                if not p.is_new():
                    continue
                candidates.append((0, 0.0, card))
            elif mode == StudyMode.WEAK:
                if p.attempts == 0 or p.best_score >= pass_score:
                    continue
                candidates.append((1, float(p.best_score), card))
            elif mode == StudyMode.ALL:
                candidates.append((2, float(p.best_score), card))
            else:  # DUE
                if not p.is_new() and not p.is_due(now):
                    continue
                priority = 0 if p.is_new() else 1
                due_ts = _parse_iso(p.due_at)
                overdue = -(due_ts.timestamp() if due_ts else 0)
                candidates.append((priority, overdue, card))

        if mode == StudyMode.WEAK:
            candidates.sort(key=lambda x: (x[1], x[0]))
        elif mode == StudyMode.DUE:
            candidates.sort(key=lambda x: (x[0], x[1]))
        elif mode == StudyMode.NEW:
            pass
        else:
            candidates.sort(key=lambda x: x[1])

        return [card for _, _, card in candidates[:limit]]

    def card_history(self, deck: Deck, card_id: str) -> list[AnswerRecord]:
        return self.get(deck, card_id).history

    # backward compat alias
    def next_cards(self, deck: Deck, limit: int = 50) -> list:
        return self.build_queue(deck, StudyMode.DUE, limit=limit)

    def update(self, deck: Deck, progress: CardProgress, pass_score: int) -> None:
        progress.mastered = progress.interval_days >= 7 and progress.best_score >= pass_score
        self.data.setdefault(self.deck_key(deck), {})[progress.card_id] = progress
        self.save()

    def reconcile_deck(self, deck: Deck, pass_score: int) -> None:
        """Пересчитать mastered (интервал ≥ 7 дней) для записей progress.json."""
        key = self.deck_key(deck)
        changed = False
        for prog in self.data.get(key, {}).values():
            new_val = prog.interval_days >= 7 and prog.best_score >= pass_score
            if prog.mastered != new_val:
                prog.mastered = new_val
                changed = True
        if changed:
            self.save()
