"""Shared minimum coverage for lessons in profession curricula."""

QA_TARGET = 8
LIVE_TARGET = 3
PROFESSION_QA_TARGET = 20
PROFESSION_LIVE_TARGET = 10


def card_targets(syllabus, qa=None, live=None):
    defaults = (PROFESSION_QA_TARGET, PROFESSION_LIVE_TARGET) if syllabus.track else (QA_TARGET, LIVE_TARGET)
    targets = [defaults[0] if qa is None else qa, defaults[1] if live is None else live]
    if syllabus.track:
        targets = [max(target, minimum) for target, minimum in zip(targets, defaults)]
    return {'qa': targets[0], 'live': targets[1] if syllabus.has_practice else 0}
