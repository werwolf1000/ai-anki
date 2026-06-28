#!/usr/bin/env python3
"""Generate Agile, Scrum, Kanban, and SAFe theory decks for AI Anki."""
from __future__ import annotations

import json
from pathlib import Path


def theory(q: str, ref: str) -> dict:
    return {"question": q, "reference": ref}


def scenario(q: str, ref: str) -> dict:
    return {"question": q, "reference": ref, "card_type": "text"}


def compare(a: str, b: str, ref: str) -> dict:
    return theory(f"Чем {a} отличается от {b}?", ref)


def dedupe(cards: list[dict]) -> list[dict]:
    seen: set[str] = set()
    out: list[dict] = []
    for c in cards:
        key = c.get("question", "") + c.get("reference", "")
        if key in seen:
            continue
        seen.add(key)
        out.append(c)
    return out


def build_agile() -> list[dict]:
    cards: list[dict] = [
        theory("Что такое Agile?", "Подход к разработке и управлению работой, основанный на итерациях, обратной связи, сотрудничестве и готовности к изменениям. Не один метод, а семейство практик и ценностей."),
        theory("Четыре ценности Agile Manifesto (2001)?", "Люди и взаимодействие важнее процессов и инструментов; работающий продукт важнее исчерпывающей документации; сотрудничество с заказчиком важнее согласования контракта; готовность к изменениям важнее следования плану."),
        theory("Как читать формулировки Manifesto «X важнее Y»?", "Это не отрицание Y, а приоритет: обе стороны ценны, но в неопределённости выбираем левую."),
        theory("12 принципов Agile Manifesto — суть?", "Ранняя и частая поставка ценности, приветствие изменений, частые релизы, ежедневное сотрудничество бизнеса и разработки, мотивированные люди, личное общение, работающий продукт как мера прогресса, устойчивый темп, техническое совершенство, простота, самоорганизующиеся команды, регулярная рефлексия."),
        theory("Что такое итеративная разработка?", "Повторяющиеся циклы, в каждом из которых создаётся приращение ценности и собирается обратная связь."),
        theory("Что такое инкрементальный подход?", "Продукт растёт по частям; каждая часть добавляет ценность, а не только «подготовительную работу»."),
        theory("Что такое MVP?", "Minimum Viable Product — минимальная версия, достаточная для проверки гипотезы ценности у реальных пользователей."),
        theory("MVP vs MMF?", "MVP — эксперимент/проверка гипотезы. MMF (Minimum Marketable Feature) — минимальный набор, который уже можно продавать или выпускать на рынок."),
        theory("Что такое user story?", "Краткое описание ценности с точки зрения пользователя: «Как [роль], я хочу [цель], чтобы [выгода]»."),
        theory("Формат INVEST для user story?", "Independent, Negotiable, Valuable, Estimable, Small, Testable — критерии качества формулировки истории."),
        theory("Что такое acceptance criteria?", "Проверяемые условия, при которых история считается выполненной. Часто Given/When/Then (BDD)."),
        theory("Epic vs Feature vs User Story?", "Epic — крупная инициатива; Feature — функциональный блок; Story — единица планирования и поставки в спринте/итерации."),
        theory("Что такое product backlog?", "Приоритизированный список всего, что может понадобиться продукту: функции, исправления, исследования, технический долг."),
        theory("Кто приоритизирует backlog в Agile?", "Product Owner / Product Manager — ответственность за порядок и максимизацию ценности."),
        theory("Что такое Definition of Ready (DoR)?", "Согласованные критерии, при которых элемент backlog готов к взятию в работу (понятность, оценка, зависимости, AC)."),
        theory("Что такое Definition of Done (DoD)?", "Согласованные критерии завершённости: код, тесты, ревью, документация, деплой — что значит «готово» для команды."),
        theory("DoR vs DoD?", "DoR — можно начинать работу; DoD — работа действительно завершена и пригодна для релиза/инкремента."),
        theory("Что такое story points?", "Относительная оценка сложности/объёма/риска, а не часы. Используется для планирования ёмкости, не как KPI производительности людей."),
        theory("Planning Poker — зачем?", "Коллективная оценка story points с обсуждением расхождений — снижает bias и улучшает понимание задачи."),
        theory("Velocity — что это?", "Сумма story points, завершённых командой за итерацию. Прогнозный инструмент, не цель для «увеличения любой ценой»."),
        theory("Что такое WIP limit в Agile-контексте?", "Ограничение незавершённой работы для фокуса и потока; центральная практика Kanban, полезна и в Scrum."),
        theory("Что такое continuous delivery?", "Способность часто и предсказуемо выпускать изменения в production с автоматизацией и качеством."),
        theory("CI vs CD?", "CI — частая интеграция и автоматические проверки. CD — доставка до staging/production по pipeline."),
        theory("Что такое technical debt?", "Компромиссы в коде/архитектуре, ускоряющие сейчас, но замедляющие изменения позже. Управляется явно в backlog."),
        theory("Refactoring в Agile?", "Постоянное улучшение структуры кода без изменения поведения — часть устойчивого темпа."),
        theory("Что такое cross-functional team?", "Команда со всеми навыками для создания инкремента без постоянной внешней зависимости по каждой задаче."),
        theory("Что такое self-organizing team?", "Команда сама решает, как выполнить работу в рамках целей; лидерство распределено, не микроменеджмент."),
        theory("Роль менеджера в Agile?", "Создавать условия, снимать impediments, защищать фокус, развивать систему — не распределять задачи по часам."),
        theory("Что такое stakeholder?", "Любой, кто заинтересован в продукте: пользователи, бизнес, compliance, поддержка, продажи."),
        theory("Что такое feedback loop?", "Короткий цикл «сделали → показали → узнали → скорректировали» — основа адаптации."),
        theory("Build-measure-learn (Lean Startup)?", "Цикл проверки гипотез: создать эксперiment/MVP → измерить → принять решение pivot/persevere."),
        theory("Pivot vs persevere?", "Pivot — смена гипотезы/направления на основе данных; persevere — продолжать текущую стратегию."),
        theory("Что такое Lean?", "Философия устранения потерь (muda) и максимизации ценности для клиента с минимальным WIP и pull."),
        theory("7 видов потерь (muda) в разработке?", "Частично: ожидание, передачи, лишняя функциональность, дефекты, переключение контекста, незавершённая работа, неиспользованный потенциал людей."),
        theory("Что такое Kaizen?", "Непрерывное улучшение маленькими шагами через регулярную рефлексию и эксперiments."),
        theory("Что такое retrospective?", "Регулярная встреча команды: что хорошо, что улучшить, конкретные действия на следующий цикл."),
        theory("Start-Stop-Continue?", "Формат ретро: что начать, что прекратить, что продолжить."),
        theory("4L retrospective?", "Liked, Learned, Lacked, Longed for."),
        theory("Что такое impediment?", "Препятствие, мешающее команде выполнить работу; должно быть видимым и эскалируемым."),
        theory("Что такое timebox?", "Фиксированный максимальный интервал времени на активность; по окончании — решение на основе имеющегося результата."),
        theory("Что такое incremental funding?", "Финансирование по этапам ценности вместо большого upfront-бюджета на весь проект."),
        theory("Agile vs Waterfall — ключевое?", "Waterfall предполагает предсказуемость требований; Agile — эмпирическое управление при неопределённости."),
        theory("Empirical process control?", "Прозрачность, инспекция, адаптация — управление через наблюдение реальности, а не только план."),
        theory("Transparency в Agile?", "Работа, риски, прогресс видны заинтересованным сторонам (доска, backlog, метрики потока)."),
        theory("Inspection?", "Регулярный пересмотр артеfactов и процесса (review, retro, daily sync)."),
        theory("Adaptation?", "Корректировка планов, backlog, процесса по результатам inspection."),
        theory("Что такое servant leadership?", "Лидерство через служение команде: убрать блокеры, развить автономию, создать безопасность."),
        theory("Psychological safety?", "Уверенность, что можно ошибаться, задавать вопросы и не соглашаться без наказания — основа обучения."),
        theory("Что такое pair programming?", "Два разработчика за одной задачей: driver + navigator; повышает качество и распространение знаний."),
        theory("Mob programming?", "Вся команда работает над одной задачей одновременно."),
        theory("TDD в Agile?", "Test-Driven Development: тест → минимальный код → рефакторинг; поддерживает частые изменения."),
        theory("Что такое spike?", "Timeboxed исследование для снижения неопределённости перед реализацией."),
        theory("Что такое enabler story?", "История, создающая инфраструктуру/архитектуру для будущих user stories."),
        theory("Bug vs defect в backlog?", "Дефект — несоответствие ожиданиям; обрабатывается по severity и SLA, может идти в sprint или отдельный поток."),
        theory("Что такое release train (общее)?", "Ритм регулярных релизов; в SAFe — Program Increment; в Kanban — cadence поставки."),
        theory("Outcome vs output?", "Output — сколько сделали; outcome — какой результат для пользователя/бизнеса. Agile фокусируется на outcome."),
        theory("OKR и Agile?", "OKR задают направление и амбициозные результаты; backlog и итерации — тактическое исполнение."),
        theory("Что такое value stream?", "Последовательность шагов от идеи до ценности у клиента; цель — сократить lead time и потери."),
        theory("Batch size — почему меньше лучше?", "Меньшие партии быстрее проходят систему, снижают риск и ускоряют обратную связь."),
        theory("Что такое forecasting в Agile?", "Прогноз на основе throughput/velocity и диапазонов, а не точной Gantt-даты на год."),
        theory("Monte Carlo forecasting?", "Статистический прогноз сроков по историческому throughput и оставшемуся объёму."),
        theory("#NoEstimates — идея?", "Планировать по размеру элементов и фактическому потоку, минимизируя costly estimation там, где throughput достаточен."),
        theory("Что такое discovery vs delivery?", "Discovery — понять проблему и гипотезы; delivery — реализовать проверенное решение."),
        theory("Dual-track Agile?", "Параллельные discovery и delivery tracks с постоянной связью."),
        theory("Что такое design thinking в связке с Agile?", "Empathize → Define → Ideate → Prototype → Test до/вместе с delivery."),
        compare("Agile", "Scrum", "Agile — зонтичные ценности и принципы. Scrum — конкретный фреймворк с ролями, событиями и артеfactами."),
        compare("Agile", "Kanban", "Agile — мышление и принципы. Kanban — метод управления потоком работы с визуализацией и WIP limits."),
        compare("Scrum", "Kanban", "Scrum — фиксированные спринты и роли. Kanban — непрерывный поток, эволюционные изменения, акцент на метриках потока."),
        compare("Story points", "часы", "Points — относительная сложность для планирования ёмкости. Часы — конкретное время; смешивать как KPI людей нельзя."),
        compare("Lead time", "cycle time", "Lead time — от запроса до доставки клиенту. Cycle time — от начала работы до завершения."),
        scenario(
            "Команда закрыла 40 story points, но пользователи не используют фичу. Что не так с фокусом?",
            "Фокус на output (points) вместо outcome. Нужны метрики использования, гипотезы ценности, discovery и связь с OKR.",
        ),
        scenario(
            "Менеджер требует увеличить velocity каждый спринт. Какой риск?",
            "Gaming метрики, падение качества, выгорание. Velocity — для прогноза, не KPI. Лучше улучшать поток и DoD.",
        ),
        scenario(
            "Backlog на 2 года, команда не знает, с чего начать. Первый шаг?",
            "Явная приоритизация по ценности/риску, thin slicing, ближайшие 1–2 итерации детализировать, остальное — грубо.",
        ),
    ]

    topics = [
        ("рефакторинг", "постоянное улучшение кода без смены поведения"),
        ("автотесты", "быстрая обратная связь и безопасные изменения"),
        ("code review", "совместное качество и распространение знаний"),
        ("trunk-based development", "короткоживущие ветки и частая интеграция"),
        ("feature flags", "деплой без немедленного включения для пользователей"),
        ("A/B тест", "сравнение вариантов на реальных пользователях"),
        ("customer interview", "качественное discovery и проверка проблем"),
        ("impact mapping", "связь целей, акторов, impacts и deliverables"),
        ("story mapping", "визуализация пользовательского пути и релизов"),
        ("Kano model", "классификация must-be, performance, delighters"),
        ("RICE prioritization", "Reach, Impact, Confidence, Effort для порядка backlog"),
        ("MoSCoW", "Must, Should, Could, Won't — грубая приоритизация"),
        ("cost of delay", "экономический вес откладывания работы"),
        ("Little's Law", "WIP = Throughput × Cycle Time — связь метрик потока"),
        ("flow efficiency", "доля времени активной работы vs общего lead time"),
    ]
    for name, desc in topics:
        cards.append(theory(f"Как {name} связан с Agile?", f"{name.capitalize()}: {desc}."))
        cards.append(theory(f"Когда применять {name}?", f"Когда нужно {desc} в условиях частых изменений и фокуса на ценности."))

    principles = [
        "ранняя поставка ценности",
        "приветствие изменений требований",
        "устойчивый темп работы",
        "лица-to-face коммуникация",
        "самоорганизация команд",
        "простота — искусство не делать лишнего",
        "регулярная рефлексия и настройка",
    ]
    for p in principles:
        cards.append(theory(f"Принцип Agile: {p} — практический смысл?", f"В работе команды это означает сознательный выбор в пользу {p} при trade-offs."))

    anti = [
        ("Agile = без документации", "Manifesto не отменяет документацию — нужна «достаточная», живая и полезная."),
        ("Agile = хаос", "Agile опирается на дисциплину прозрачности, DoD, ритмы и эмпирическое управление."),
        ("Agile только для IT", "Применим везде, где неопределённость и нужна адаптация: маркeting, HR, hardware."),
        ("Sprint = mini-waterfall", "Спринт должен давать инкремент и обратную связь, а не только фазы анализа/теста в конце."),
    ]
    for myth, ref in anti:
        cards.append(theory(f"Миф: «{myth}» — верно?", ref))

    cards.extend(bulk_terms("Agile", [
        ("iteration", "Фиксированный или timeboxed цикл разработки с поставкой результата."),
        ("increment", "Приращение ценности продукта, соответствующее DoD."),
        ("backlog grooming", "Устаревший термин; сейчас backlog refinement — уточнение элементов backlog."),
        ("planning onion", "Стратегия → release → sprint → daily — разные горизонты планирования."),
        ("information radiator", "Видимый дашборд/доска статуса для всех (Big Visible Chart)."),
        ("osborne effect", "Риск: анонс фичи снижает продажи текущей версии — учитывать в roadmap."),
        ("smurf account", "Anti-pattern: один человек делает всё критичное — bus factor 1."),
        ("bus factor", "Сколько людей можно «потерять» без остановки команды."),
        ("YAGNI", "You Aren't Gonna Need It — не строить функциональность «на будущее» без need."),
        ("KISS", "Keep It Simple — простое решение предпочтительнее сложного."),
        ("DRY", "Don't Repeat Yourself — устранять дублирование знаний в коде."),
        ("Boy Scout Rule", "Оставь код чище, чем нашёл — микро-рефакторинг постоянно."),
        ("fail fast", "Быстро получить сигнал об ошибке гипотезы, чтобы дешевле pivot."),
        ("gemba", "«Место работы» — идти к пользователям/команде, а не только отчёты."),
        ("gemba walk", "Наблюдение процесса на месте для понимания реальности."),
        ("Hoshin Kanri", "Стратегическое выравнивание целей организации и команд."),
        ("Obeya", "Большая комната/стена для визуального управления программой."),
        ("cadence", "Регулярный ритм событий (planning, review) для predictability."),
        ("heartbeat", "Синхронизация команд через общий cadence (как PI в SAFe)."),
        ("work item aging", "Время с момента старта/создания item — индикатор застоя."),
        ("slack capacity", "Запас ёмкости (~20%) на непредвиденное и improvement."),
        ("slack time", "Выделенное время на обучение и улучшения внутри итерации."),
        ("scope creep", "Некontrolled рост scope без пересмотра приоритетов."),
        ("gold plating", "Добавление «красоты» сверх нужной ценности."),
        ("analysis paralysis", "Застревание в анализе без delivery и feedback."),
        ("HIPPO", "Highest Paid Person's Opinion — anti-pattern приоритизации без data."),
        ("feature factory", "Команда выпускает фичи без проверки outcome."),
        ("success theater", "Метрики активности вместо реальных результатов."),
        ("cargo cult Agile", "Ритуалы без ценностей: доска есть, мышления нет."),
        ("wagile", "Waterfall disguised as Agile — phases внутри «sprint»."),
        ("sustainable pace", "Темп, который команда может держать indefinitely без burnout."),
        ("whole team approach", "QA, dev, design вместе от discovery до release."),
        ("shift-left", "Раньше вносить quality, security, testing в процесс."),
        ("shift-right", "Production monitoring и эксперiments после release."),
        ("Definition of Fun", "Командное соглашение о том, как работать с удовольствием."),
        ("working agreement", "Явные правила коммуникации и collaboration команды."),
        ("team charter", "Миссия, values, working agreements команды."),
        ("social contract", "Нормы поведения на ретро, daily, review."),
        ("delegation poker", "Уровни делегирования решений (7 levels) для PO/manager."),
        ("liberating structures", "Набор форматов встреч для inclusive facilitation."),
        ("open space", "Unconference формат: agenda на месте участниками."),
        ("world café", "Ротация групп для обсуждения тем."),
        ("lean coffee", "Agenda vote участниками на начало встречи."),
        ("fishbowl", "Малый круг обсуждает, остальные слушают и могут войти."),
        ("premortem", "До старта: представить провал и причины — снизить риски."),
        ("postmortem", "Разбор инцидента без blame для learning."),
        ("blameless postmortem", "Фокус на системе, не на наказании людей."),
        ("five whys", "Корневая причина через цепочку «почему»."),
        ("A3 report", "Lean формат problem-solving на одной странице."),
        ("PDCA", "Plan-Do-Check-Act — цикл улучшения Deming."),
        ("OODA loop", "Observe-Orient-Decide-Act — быстрая адаптация в uncertainty."),
    ]))

    return dedupe(cards)


def bulk_terms(prefix: str, items: list[tuple[str, str]]) -> list[dict]:
    return [theory(f"{prefix}: что такое {term}?", definition) for term, definition in items]


def build_scrum() -> list[dict]:
    cards: list[dict] = [
        theory("Что такое Scrum?", "Лёгкий фреймворк для решения сложных адаптивных задач через короткие итерации (Sprint), прозрачность и эмпирический контроль."),
        theory("Три столпа Scrum?", "Transparency, Inspection, Adaptation."),
        theory("Три роли Scrum?", "Product Owner, Scrum Master, Developers (Scrum Team)."),
        theory("Product Owner — ответственность?", "Максимизация ценности продукта, управление Product Backlog, приоритизация, ясность элементов."),
        theory("Может ли PO быть несколько человек?", "В Scrum один PO на продукт (может делегировать, но accountability един)."),
        theory("Scrum Master — ответственность?", "Эффективность Scrum: фасilitация, coaching, устранение impediments, работа с организацией."),
        theory("SM vs project manager?", "SM не управляет людьми и сроками задач; служит процессу и команде, не «начальник»."),
        theory("Developers в Scrum?", "Cross-functional профессионалы, создающие Increment; сами commit и plan sprint backlog."),
        theory("Scrum Team size?", "Обычно до 10 человек; при большем масштабе — несколько команд на одном продукте."),
        theory("Что такое Sprint?", "Timebox до 1 месяца (часто 2 недели), в котором создаётся Done Increment."),
        theory("Можно ли менять Sprint Goal mid-sprint?", "Не менять scope так, чтобы нарушить цель; scope negotiation с PO при новых insights."),
        theory("Sprint Goal?", "Единая цель спринта — «зачем этот спринт»; фокус команды и критерий гибкости scope."),
        theory("События Scrum?", "Sprint, Sprint Planning, Daily Scrum, Sprint Review, Sprint Retrospective."),
        theory("Sprint Planning — цель?", "Определить Sprint Goal, выбрать backlog items, спланировать работу на Sprint."),
        theory("Daily Scrum — цель?", "15 мин sync: прогресс к Sprint Goal, план на день, impediments. Не status report менеджеру."),
        theory("Три вопроса Daily (классика)?", "Что сделал? Что сделаю? Что мешает? (в 2020+ Scrum Guide акцент на Goal, не обязательно три вопроса)."),
        theory("Sprint Review — цель?", "Inspect Increment и backlog с stakeholders; адаптировать Product Backlog."),
        theory("Sprint Retrospective — цель?", "Inspect людей, взаимодействий, процесса, tools; план улучшений."),
        theory("Артеfactы Scrum?", "Product Backlog, Sprint Backlog, Increment."),
        theory("Product Backlog?", "Emergent, ordered list всего для продукта; единственный источник работы для Scrum Team."),
        theory("Sprint Backlog?", "Цель спринта + выбранные PB items + план доставки (often task board)."),
        theory("Increment?", "Конкретная проверяемая работа в соответствии с DoD; сумма всех Done items в Sprint + предыдущие."),
        theory("DoD на уровне организации?", "Минимум качества для любого Increment; команда может ужесточать, не ослаблять."),
        theory("Backlog refinement?", "Ongoing activity: декомпозиция, оценка, уточнение — обычно ≤10% capacity, не обязательное event."),
        theory("Commitment в Sprint Planning?", "Developers commit на Sprint Backlog; PO commit на ценность и порядок PB."),
        theory("Who can cancel Sprint?", "Only Product Owner, если цель устарела — rare."),
        theory("Scrum of Scrums?", "Sync нескольких Scrum-команд: представители обсуждают зависимости и интеграцию."),
        theory("Nexus framework?", "Scrum.org scaling: Nexus Integration Team, Nexus Sprint, dependencies между 3–9 teams."),
        theory("LeSS?", "Large-Scale Scrum: один PO, один backlog, feature teams, общие sprint."),
        theory("Scrum@Scale?", "Scaling через Scrum of Scrums и Executive Action Team."),
        compare("Sprint Review", "Demo", "Review — inspect & adapt с stakeholders и backlog; demo — часть показа Increment, не вся встреча."),
        compare("Sprint Backlog", "Kanban board", "Sprint Backlog — scope спринта; Kanban board может показывать flow с WIP limits вне спринта."),
        compare("PO", "Project sponsor", "PO отвечает за ценность продукта day-to-day; sponsor — funding и стратегические решения."),
        scenario(
            "На Daily 45 минут, все докладывают PO. Проблема?",
            "Daily превратился в status meeting. Вернуть 15 min timebox, фокус на Sprint Goal, impediments — offline sync.",
        ),
        scenario(
            "Increment не соответствует DoD, но PO хочет релиз. Что делать?",
            "DoD не negotiable для Increment. Либо довести до Done, либо явно не считать Done (technical debt, риск).",
        ),
        scenario(
            "Команда не успевает Sprint Goal за 2 дня до конца. Действия?",
            "Collaborate с PO: scope negotiation, focus on Goal, не «добавить людей» blindly; retro причин.",
        ),
        scenario(
            "SM пишет задачи каждому разработчику. Это Scrum?",
            "Нет — нарушение self-management Developers. SM должен coach, не распределять work.",
        ),
    ]

    events_detail = [
        ("Sprint Planning", "определить Why (Goal), What (PB items), How (plan)"),
        ("Daily Scrum", "адаптировать план на 24ч к Sprint Goal"),
        ("Sprint Review", "получить feedback, обновить backlog"),
        ("Sprint Retrospective", "1–3 улучшения процесса на следующий sprint"),
    ]
    for ev, detail in events_detail:
        cards.append(theory(f"Кто обязан участвовать в {ev}?", "Scrum Team; Review также stakeholders; PO ключевой на Planning и Review."))
        cards.append(theory(f"Timebox {ev}?", "Для 1-month sprint: Planning 8h, Review 4h, Retro 3h, Daily 15m; пропорционально для shorter sprints."))
        cards.append(theory(f"Output {ev}?", detail))

    pb_items = [
        "user story", "bug", "technical debt", "spike", "research", " enabler", " compliance item",
    ]
    for item in pb_items:
        cards.append(theory(f"Может ли {item.strip()} быть в Product Backlog?", "Да — PB содержит всё, что нужно продукту; PO приоритизирует прозрачно."))

    scaling = [
        ("feature team", "команда end-to-end по фиче, не component team"),
        ("component team", "риск зависимостей и медленного flow при масштабировании Scrum"),
        ("integration sprint", "anti-pattern — частые интеграции каждый sprint предпочтительнее"),
        ("hardening sprint", "anti-pattern — качество должно быть в каждом Increment via DoD"),
    ]
    for term, ref in scaling:
        cards.append(theory(f"Scrum scaling: {term}?", ref))

    metrics = [
        ("Sprint Goal success", "достигнута ли цель, не только closed points"),
        ("escaped defects", "качество Increment после release"),
        ("team happiness", "индикатор устойчивости"),
        ("cycle time per story", "поток внутри спринта"),
    ]
    for m, ref in metrics:
        cards.append(theory(f"Полезная метрика Scrum: {m}?", ref))

    cards.extend(bulk_terms("Scrum", [
        ("forecast", "Прогноз completion на основе velocity и оставшегося backlog."),
        ("release planning", "Optional: horizon beyond sprint; не replace sprint planning."),
        ("Sprint backlog item", "Unit work на sprint board; может быть task sub-items."),
        ("task", "Разбиение story для tracking; не обязательны в Scrum Guide."),
        ("impediment backlog", "Visible list блокеров для SM/организации."),
        ("Scrum board", "Visual Sprint Backlog: To Do, Doing, Done."),
        ("burndown", "Remaining work vs time in sprint."),
        ("burnup", "Completed vs total scope — виден scope change."),
        ("release burndown", "Across sprints до release milestone."),
        ("velocity range", "Min-max velocity для probabilistic forecast."),
        ("capacity", "Available person-days в sprint minus meetings, PTO."),
        ("focus factor", "Доля capacity на sprint work vs overhead."),
        ("committed scope", "Items team agrees to deliver toward Sprint Goal."),
        ("uncommitted backlog", "PB items not in current sprint."),
        ("emergent architecture", "Architecture evolves через increments, не big design upfront."),
        ("ScrumBut", "«We do Scrum, but…» — compromises без понимания why."),
        ("ScrumAnd", "Добавление practices (Kanban, XP) поверх Scrum framework."),
        ("Done column", "Items meeting DoD — потенциально shippable."),
        ("technical story", "Story для refactoring, tooling — должна давать value или enabler."),
        ("Scrum poker", "Same as Planning Poker — consensus estimation."),
        ("affinity estimation", "Группировка stories по размеру без чисел."),
        ("T-shirt sizing", "S/M/L/XL для грубой оценки epics/features."),
        ("ideal days", "Оценка в «идеальных днях» — осторожно, не равно calendar."),
        ("Sprint cancellation", "PO решает; done items review, rest re-estimate в PB."),
        ("part-time PO", "Risk: backlog starvation; нужен delegate или proxy."),
        ("proxy PO", "Временный представитель — должен иметь authority."),
        ("component team", "Team по слою (UI, API) — dependency overhead в Scrum."),
        ("feature team", "End-to-end delivery — предпочтительнее at scale."),
        ("Scrum Master as team admin", "Anti-pattern — SM не Jira- secretary only."),
        ("rotating SM", "Possible но теряется dedicated improvement focus."),
        ("Scrum of Scrums Master", "Facilitates multi-team sync."),
        ("integration team", "Dedicated integration — signal weak CI/CD на ART level."),
        ("Scrum values: Courage", "Говорить правду о scope, quality, risks."),
        ("Scrum values: Focus", "На Sprint Goal, не на random work."),
        ("Scrum values: Openness", "Прозрачность work, проблем, learning."),
        ("Scrum values: Respect", "К коллегам, stakeholders, users."),
        ("Scrum values: Commitment", "К Sprint Goal и team goals, не к scope любой ценой."),
        ("Scrum Guide", "Official definition Scrum by Ken Schwaber & Jeff Sutherland."),
        ("empirical process", "Decisions on observation, not only plan."),
        ("complex work", "Domain где analysis не даёт full answer upfront — Scrum sweet spot."),
        ("ordered backlog", "PB strictly ordered — top = highest value next."),
        ("transparency of backlog", "Visible, understood by Scrum Team and stakeholders."),
        ("Sprint timebox max", "One month or less — чаще 1–4 weeks."),
        ("consecutive Sprints", "No gap — next starts immediately after previous."),
        ("Sprint consistency", "Same length sprints для rhythm и metrics."),
        ("stakeholder collaboration", "Key на Review — feedback loop."),
        ("incremental delivery", "Each sprint adds Done work on previous increments."),
        ("potentially releasable", "Increment meets DoD — может go live if PO decides."),
        ("technical debt in sprint", "Allocate capacity — не только features."),
        ("bug fix in sprint", "Part of work — PO prioritizes in PB."),
        ("Scrum Master removing impediments", "Org-level blockers — SM escalates."),
        ("Developers self-assign", "Team pulls work — не manager assigns tasks."),
        ("cross-skilling", "Developers learn adjacent skills — reduce bottlenecks."),
        ("specialist", "Allowed но team collective ownership on Sprint Goal."),
        ("Scrum in regulated industry", "DoD includes validation; documentation as needed."),
        ("Scrum with offshore", "Overlap hours, clear DoD, strong refinement."),
        ("Scrum anti-pattern: zombie Scrum", "Mechanical events без improvement и value."),
    ]))

    return dedupe(cards)


def build_kanban() -> list[dict]:
    cards: list[dict] = [
        theory("Что такое Kanban (метод)?", "Метод улучшения workflow: визуализация, WIP limits, управление flow, явные policies, feedback loops, эволюционные изменения."),
        theory("Kanban vs Kanban board?", "Board — инструмент визуализации. Kanban Method — система управления знанием работы (David J. Anderson)."),
        theory("Шесть практик Kanban?", "Visualize, Limit WIP, Manage Flow, Make Policies Explicit, Implement Feedback Loops, Improve Collaboratively (evolve experimentally)."),
        theory("Pull system?", "Работа начинается, когда есть capacity downstream — сигнал «взять следующее», а не push сверху."),
        theory("Push vs pull?", "Push — назначают работу независимо от capacity. Pull — следующая задача при освобождении слота/WIP."),
        theory("WIP limit — зачем?", "Снижает multitasking, выявляет bottlenecks, ускоряет flow, делает проблемы видимыми."),
        theory("Что происходит при превышении WIP?", "Команда фокусируется на завершении текущего, не берёт новое — или явно эскалирует policy exception."),
        theory("Classes of Service?", "Expedite, Fixed Date, Standard, Intangible — разные правила приоритета и WIP для типов работы."),
        theory("Expedite lane?", "Срочный класс с отдельным WIP (often 1); злоупотребление разрушает predictability."),
        theory("Fixed Date CoS?", "Работа с дедлайном — планирование backward от даты, может обгонять standard."),
        theory("Intangible class?", "Техдолг, улучшения — часто без жёсткого SLA, но критично для long-term flow."),
        theory("Cumulative Flow Diagram (CFD)?", "График count items по состояниям во времени; расширение band = WIP/задержки."),
        theory("Cycle time chart?", "Распределение времени от start до done; для SLA и predictability."),
        theory("Throughput?", "Количество завершённых items за период (week/month)."),
        theory("Lead time в Kanban?", "От commitment/запроса до delivery — ключевая customer metric."),
        theory("Cycle time в Kanban?", "От start work до done — процессная метрика."),
        theory("Little's Law в Kanban?", "Avg WIP = Throughput × Avg Cycle Time — для диагностики системы."),
        theory("Blockers на board?", "Явно помечать blocked items; track blocked time отдельно."),
        theory("Swimlanes?", "Горизонтальные дорожки по классу работы, команде, продукту — для clarity."),
        theory("Columns vs states?", "Column — визуал; state — реальное правило перехода (может быть sub-columns)."),
        theory("Definition of Workflow?", "Kanban equivalent policies: когда item ready, что значит each column, WIP per column."),
        theory("STATIK — что это?", "Systems Thinking Approach to Introducing Kanban: источники неудовлетворённости, demand analysis, capability, workflow design."),
        theory("Service Delivery Manager?", "Роль фокуса на flow metrics, policies, predictability (аналог SM в Kanban context)."),
        theory("Replenishment meeting?", "Populating ready queue — когда и сколько items pull в систему."),
        theory("Kanban meeting (standup)?", "Обход board справа налево: finish, help, flow — не round-robin people."),
        theory("Risk review?", "Анализ aging items, blockers, классов service."),
        theory("Operations review?", "Метрики между teams/services — throughput, lead time trends."),
        theory("Strategy review?", "Связь portfolio и Kanban system на верхнем уровне."),
        theory("Evolutionary change vs transformation?", "Kanban начинает с текущего процесса и улучшает incrementally, без big-bang reorg."),
        theory("Scrumban?", "Scrum events + Kanban flow/WIP; гибкий hybrid для зрелых команд."),
        compare("Kanban", "Scrum", "Kanban — continuous flow, optional roles/events. Scrum — fixed sprints, defined accountabilities."),
        compare("WIP limit", "team capacity", "WIP — explicit constraint на колонку/систему; capacity — люди/часы; WIP управляет flow напрямую."),
        compare("Commitment point", "backlog", "Commitment point — где item enters система и starts lead time clock."),
        scenario(
            "CFD: band «In Progress» steadily widening. Диагноз?",
            "WIP растёт, завершение не успевает — bottleneck или слишком высокий WIP limit; focus on finish.",
        ),
        scenario(
            "Все items Expedite. Что делать?",
            "Пересмотреть CoS policy; expedite WIP=1; обучить stakeholders cost of delay.",
        ),
        scenario(
            "Lead time 30 days, cycle time 3 days. Где потери?",
            "27 days waiting — queue before start; улучшать replenishment, prioritization, WIP до «In Progress».",
        ),
    ]

    columns = [
        "Backlog", "Ready", "Analysis", "Development", "Review", "Test", "Done", "Production",
    ]
    for i, col in enumerate(columns[:-1]):
        nxt = columns[i + 1]
        cards.append(theory(f"Policy перехода «{col} → {nxt}» — что типично?", f"Explicit criteria: что должно быть выполнено в «{col}» перед pull в «{nxt}»."))

    metrics_q = [
        ("85th percentile cycle time", "SLA «85% items done within X days»"),
        ("aging WIP chart", "items с long cycle time в work — риск"),
        ("blocked time", "сколько flow теряется на dependencies"),
        ("flow efficiency", "active time / lead time"),
    ]
    for m, ref in metrics_q:
        cards.append(theory(f"Метрика Kanban: {m}?", ref))

    anti = [
        ("Kanban = no planning", "Есть replenishment и cadence; planning не исчезает, становится pull-based."),
        ("Kanban = no deadlines", "Fixed Date CoS явно работает с deadlines."),
        ("Visual board enough", "Без WIP limits и policies это просто sticky notes."),
    ]
    for myth, ref in anti:
        cards.append(theory(f"Kanban myth: {myth}?", ref))

    cards.extend(bulk_terms("Kanban", [
        ("visualize workflow", "Первая практика — сделать невидимую работу видимой."),
        ("limit WIP", "Constraint на количество items в каждом состоянии."),
        ("manage flow", "Оптимизация movement work, не busyness людей."),
        ("make policies explicit", "Written rules для transitions и classes of service."),
        ("feedback loops", "Cadences для inspect и adapt metrics/policies."),
        ("evolve experimentally", "Small changes, measure, keep or rollback."),
        ("Kanban lens", "Start where you are — не менять roles/events сразу."),
        ("commitment point", "Где item считается committed — start lead time."),
        ("delivery point", "Где item считается delivered customer."),
        ("work item type", "Bug, feature, chore — разные policies возможны."),
        ("ticket", "Kanban card representing unit of work."),
        ("token", "Physical limit WIP — один token на item в колонке."),
        ("CONWIP", "Constant Work In Process — classic production control."),
        ("Drum-Buffer-Rope", "Theory of Constraints scheduling — связь с pull."),
        ("bottleneck", "Constraint limiting throughput всей системы."),
        ("starvation", "Downstream idle из-за empty queue upstream."),
        ("blocking", "Item cannot proceed — explicit blocker reason."),
        ("stalled work", "In progress too long — aging signal."),
        ("splitting items", "Разделить large item для smaller cycle time."),
        ("merging items", "Combine duplicate requests."),
        ("discard policy", "When to cancel obsolete items."),
        ("done definition per column", "Exit criteria каждого state."),
        ("entry criteria", "When item allowed enter column."),
        ("queue", "Buffer before active work — often limited WIP."),
        ("activity", "Active work state — value-adding time."),
        ("wait state", "Delay between activities — waste to minimize."),
        ("value stream map", "VSM — timeline steps и wait times."),
        ("process time", "Touch time on item."),
        ("touch time", "Time actively working on item."),
        ("delay time", "Waiting in queue or blocked."),
        ("percentile", "85th/95th cycle time для SLA promises."),
        ("histogram", "Distribution cycle times — tail matters."),
        ("scatterplot", "Cycle time vs start date — aging analysis."),
        ("throughput run chart", "Completed items per week trend."),
        ("WIP run chart", "Total WIP over time — should be stable."),
        ("Monte Carlo in Kanban", "Forecast completion dates from throughput history."),
        ("forecasting delivery", "When will these 50 items finish? — probabilistic answer."),
        ("SLE", "Service Level Expectation — e.g. 85% in 8 days."),
        ("dependency board", "Track cross-team blockers explicitly."),
        ("shared services", "Specialists (DBA, UX) — отдельная Kanban queue с WIP."),
        ("two-bin system", "Replenish when bin empty — pull signal."),
        ("min-max replenishment", "Refill ready queue to max when hits min."),
        ("cadence-based delivery", "Release every Tuesday regardless — decouple from item size."),
        ("release on demand", "Ship when item done if business wants."),
        ("cost of delay distribution", "Different CoS для prioritization в triage."),
        ("sequential prioritization", "One queue order — no multitasking priorities."),
        ("emergency swap", "Expedite displaces WIP — visible cost."),
        ("Kanban Maturity Model", "0–7 levels organizational Kanban capability."),
        ("Kanban University", "Training/certification body (David Anderson)."),
        ("Triage", "Quick sort incoming by type, urgency, CoS."),
        ("Service request manager", "Role managing customer expectations и SLE."),
        ("fitness criteria", "How to judge if Kanban system serves customer well."),
        ("genba Kanban", "Shop floor cards in manufacturing origin."),
        ("just-in-time", "Produce/pull when needed — reduce inventory/WIP."),
        ("heijunka", "Leveling production — smooth flow."),
        ("andon cord", "Signal quality problem — stop line — analogy for blockers."),
        ("policy board", "Physical display of WIP limits и policies."),
        ("Scrumban planning", "Sprint goals optional + Kanban flow day-to-day."),
        ("Kanban for sales funnel", "Lead → qualified → proposal — WIP per stage."),
        ("Kanban for hiring", "Applied → interview → offer — limit open reqs."),
        ("virtual Kanban", "Same principles in tool without physical board."),
        ("portfolio Kanban", "Epics/initiatives flow at strategic level."),
        ("scaling Kanban", "Connected Kanban systems с upstream/downstream."),
    ]))

    return dedupe(cards)


def build_safe() -> list[dict]:
    cards: list[dict] = [
        theory("Что такое SAFe?", "Scaled Agile Framework — набор организационных и workflow patterns для Agile at enterprise scale."),
        theory("SAFe Big Picture — уровни?", "Team, Program (ART), Large Solution (optional), Portfolio, Full — в зависимости от конфигурации."),
        theory("Что такое ART?", "Agile Release Train — long-lived team of Agile teams (5–12), синхронизированная поставка value stream."),
        theory("RTE — роль?", "Release Train Engineer — «chief Scrum Master» train: PI planning facilitation, impediments, flow."),
        theory("System Architect/Engineer?", "Техническое направление, enablers, NFRs, архитектурный runway на ART."),
        theory("Product Management в SAFe?", "Content authority на Program level: Features, WSJF, roadmap на PI."),
        theory("Business Owners?", "Ключевые stakeholders train; assign value на PI objectives; go/no-go на ROI."),
        theory("Что такое PI (Program Increment)?", "Timebox 8–12 weeks (default 10) + Innovation & Planning (IP) iteration."),
        theory("PI Planning — суть?", "2-day event: vision, team breakouts, draft plans, dependencies, PI Objectives, confidence vote."),
        theory("PI Objectives?", "Business + team objectives на PI; SMART, measurable; used in Inspect & Adapt."),
        theory("Stretch objectives?", "Дополнительные цели при избытке capacity — явно optional."),
        theory("Team PI Objectives vs Program?", "Teams commit свои; aggregated на train level с Business Owners."),
        theory("Innovation & Planning iteration?", "Buffer для learning, hackathon, tech debt, planning next PI — no feature pressure."),
        theory("Inspect & Adapt (I&A)?", "End of PI: PI system demo, quantitative review, problem-solving workshop."),
        theory("WSJF?", "Weighted Shortest Job First: Cost of Delay / Job Size — prioritization на program/portfolio."),
        theory("Cost of Delay?", "Экономическая цена задержки: value, time criticality, risk reduction/opportunity enablement."),
        theory("Feature в SAFe?", "Program-level backlog item, декомposируется в stories на teams."),
        theory("Enabler features?", "Infrastructure, architecture, exploration — поддерживают future features."),
        theory("Architectural runway?", "Техническая подготовка на 2–3 PI вперёд для upcoming features."),
        theory("NFRs (Nonfunctional Requirements)?", "Performance, security, compliance — as backlog constraints и enablers."),
        theory("Solution Train?", "Для large solutions: несколько ARTs + suppliers, synchronized PI."),
        theory("Portfolio SAFe?", "Strategy & investment funding, lean portfolio management, value streams."),
        theory("Value stream identification?", "Operational или development value streams — кто поставляет ценность end-to-end."),
        theory("Lean Portfolio Management?", "Funding value streams, not projects; guardrails; portfolio kanban."),
        theory("Epic в SAFe?", "Large initiative; проходит portfolio kanban: funnel → review → analysis → backlog → implementing."),
        theory("Lean business case для epic?", "Оценка WSJF, cost, MVP, go/pivot/stop перед major funding."),
        theory("Guardrails?", "Budget, WIP limits, DoD на portfolio — decentralize decisions within boundaries."),
        theory("Continuous Learning Culture?", "One of SAFe core competencies — learning organization."),
        theory("Lean-Agile Leadership?", "Leaders model behaviors, empower teams, drive change."),
        theory("Team and Technical Agility?", "Scrum/Kanban, XP practices, built-in quality на team level."),
        theory("Agile Product Delivery?", "Customer centricity, design thinking, continuous delivery on ART."),
        theory("Enterprise Solution Delivery?", "Large solution coordination, suppliers, compliance."),
        theory("Lean Portfolio Management competency?", "Strategy, funding, governance aligned to flow of value."),
        theory("Organizational Agility?", "Flexible org design, lean thinking across business."),
        theory("Continuous Learning Culture competency?", "Invest in people, communities of practice, innovation."),
        theory("Built-in Quality?", "TDD, CI, pair work, architecture as code — quality не «phase at end»."),
        theory("Program backlog?", "Prioritized features/enablers для ART; owned by Product Management."),
        theory("Team backlog?", "Stories для одной Agile team в текущем PI."),
        theory("Iteration (Sprint) в SAFe?", "Default 2 weeks внутри PI; same as Scrum at team level."),
        theory("System Demo?", "End-of-iteration integrated demo across ART — real system, not team silos."),
        theory("PO Sync?", "Regular PO/PM sync dependencies и priorities across teams."),
        theory("Scrum of Scrums в SAFe?", "Coach sync / ART sync для cross-team coordination."),
        theory("ART sync?", "Weekly RTE-led: progress, risks, dependencies на train."),
        compare("PI Planning", "big upfront planning", "PI Planning — 8–12 week horizon with inspect & adapt each PI, not multi-year fixed plan."),
        compare("Feature", "Epic", "Feature — program backlog (weeks). Epic — portfolio initiative (months/quarters)."),
        compare("RTE", "Scrum Master", "RTE координирует train и PI events; SM — одну команду."),
        compare("SAFe", "LeSS", "SAFe — prescriptive framework with roles/events at scale. LeSS — minimal scaling Scrum with one backlog."),
        scenario(
            "PI Planning: confidence vote 40%. Что делать?",
            "Re-plan breakouts: resolve dependencies, scope adjustment, enablers, risks — до acceptable confidence или explicit trade-offs.",
        ),
        scenario(
            "Team завершила все stories, но System Demo broken. Проблема?",
            "Integration neglected — need CI, system team, Definition of Done на ART level, regular system demos each iteration.",
        ),
        scenario(
            "100 features in PI, teams overloaded. Root cause?",
            "WIP overload at program level; apply WSJF, reduce WIP, realistic capacity based on velocity history.",
        ),
    ]

    configs = [
        ("Essential SAFe", "Team + ART — минимальная конфигурация"),
        ("Large Solution SAFe", "+ Solution Train для complex products"),
        ("Portfolio SAFe", "+ LPM для strategy and funding"),
        ("Full SAFe", "All levels — enterprise-wide"),
    ]
    for name, desc in configs:
        cards.append(theory(f"Конфигурация {name}?", desc))

    cod = [
        ("User/business value", "WSJF numerator component"),
        ("Time criticality", "deadline/market window"),
        ("RR/OE", "Risk Reduction / Opportunity Enablement"),
        ("Job size", "WSJF denominator — estimate effort"),
    ]
    for c, ref in cod:
        cards.append(theory(f"WSJF: {c}?", ref))

    events = [
        "PI Planning", "System Demo", "Inspect & Adapt", "PO Sync", "ART Sync", "Solution Demo",
    ]
    for ev in events:
        cards.append(theory(f"Когда проводится {ev}?", f"Cadence event на program/large solution level — см. SAFe Big Picture для частоты."))

    cards.extend(bulk_terms("SAFe", [
        ("Agile Team", "5–11 members, Scrum Master, PO, devs — builds increment each iteration."),
        ("Team Backlog", "Stories для team в текущем PI."),
        ("Iteration Goals", "Team objectives aligned to PI — short term focus."),
        ("Iteration Planning", "Team plans stories for iteration like Sprint Planning."),
        ("Iteration Review", "Team demo like Sprint Review."),
        ("Iteration Retrospective", "Team improvement like Sprint Retro."),
        ("Program Increment", "8–12 week timebox для ART synchronized delivery."),
        ("PI Planning day 1", "Business context, vision, architecture, team breakouts draft."),
        ("PI Planning day 2", "Plan review, ROAM risks, confidence vote, final objectives."),
        ("ROAM", "Resolved, Owned, Accepted, Mitigated — risk categorization на PI planning."),
        ("Management review", "Part of PI planning — scope/capacity alignment."),
        ("Draft plan review", "Teams present plans, identify dependencies."),
        ("Final plan review", "Business Owners accept plan and objectives."),
        ("Program Board", "Visual PI plan: features, dependencies, milestones."),
        ("Feature timeline", "When feature expected complete across iterations."),
        ("Milestone", "Key date on program board — fixed date coordination."),
        ("Dependency", "Team A needs Team B — red string on program board."),
        ("Capacity", "Team velocity × iterations minus IP sprint."),
        ("Load vs capacity", "Compare committed features to team capacity in PI planning."),
        ("ART backlog", "Same as Program backlog — prioritized features/enablers."),
        ("Capability", "Long-lived solution area — multiple ARTs possible."),
        ("Value stream coordinator", "Coordinates multiple ARTs in value stream."),
        ("Solution Intent", "Living repository requirements, design, specs — fixed/flexible."),
        ("Fixed content", "Non-negotiable requirements in solution intent."),
        ("Variable content", "Evolving specs as learning occurs."),
        ("Model-Based Systems Engineering", "MBSE in SAFe for complex systems."),
        ("Compliance", "Regulatory needs as NFRs and enablers in backlog."),
        ("Lean UX", "SAFe UX loop: hypothesis, MVP, research, ARCHITECT collaboration."),
        ("Customer Centricity", "Design thinking, Gemba, continuous exploration."),
        ("Continuous Exploration", "Discover needs, ideate MVPs, create roadmap."),
        ("Continuous Integration", "Team/ART level frequent integration."),
        ("Continuous Deployment", "Automated release pipeline."),
        ("Continuous Release", "Release on demand to production."),
        ("DevOps", "CALMR culture in SAFe — break silos dev/ops."),
        ("System Team", "Integrates, runs system CI, supports demos across ART."),
        ("Shared Services", "Specialists supporting multiple ARTs."),
        ("Community of Practice", "Cross-ART skill sharing (architecture, testing)."),
        ("Center of Excellence", "LACE guides transformation."),
        ("Implementation roadmap", "Train execs, launch ART, expand, sustain."),
        ("Value stream KPI", "Flow, quality, satisfaction, outcomes per value stream."),
        ("Lean budget", "Fund value streams not projects — guardrails."),
        ("Epic Owner", "Guides epic through portfolio kanban."),
        ("Enterprise Architect", "Portfolio tech strategy, enabler epics."),
        ("Strategic themes", "Portfolio investment categories linked to strategy."),
        ("Portfolio vision", "Long-term direction for solutions."),
        ("Portfolio backlog", "Epics prioritized by WSJF."),
        ("Portfolio kanban", "Funnel → Reviewing → Analyzing → Backlog → Implementing."),
        ("Participatory budgeting", "Collaborative allocation across value streams."),
        ("Lean governance", "Lightweight decision rights within guardrails."),
        ("Metric: flow velocity", "Features completed per PI on ART."),
        ("Metric: flow time", "Time feature in program kanban."),
        ("Metric: flow load", "WIP features in progress on ART."),
        ("Metric: flow efficiency", "Active vs wait time on program."),
        ("Agile contracting", "SAFe guidance on outcome-based vendor contracts."),
        ("Supplier", "External team on Solution Train with same PI cadence."),
        ("Pre-PI planning", "Prep before main event — backlog readiness."),
        ("Post-PI planning", "Follow-up actions after event."),
        ("ART launch", "First PI planning kicks off new train."),
        ("Value stream launch", "Multiple ARTs aligned to stream."),
        ("SAFe Summit", "Community conference for practitioners."),
        ("SAFe practice exam", "Assessment for certification prep."),
        ("RTE sync", "Release Train Engineer coordinates SM community."),
        ("PO sync meeting", "Product owners align on priorities weekly."),
        ("Architect sync", "System architects coordinate enablers/NFRs."),
        ("Coach sync", "Scrum Masters and coaches share impediments."),
        ("Business Agility", "SAFe goal — respond rapidly to market change."),
        ("Principle: Take economic view", "Understand economic impact of decisions."),
        ("Principle: Apply systems thinking", "Optimize whole, not local."),
        ("Principle: Assume variability", "Preserve options, empirical decisions."),
        ("Principle: Build incrementally", "Fast integrated learning cycles."),
        ("Principle: Base milestones on objective evaluation", "Working systems, not documents."),
        ("Principle: Visualize WIP", "Limit batch sizes, manage queue lengths."),
        ("Principle: Apply cadence", "Synchronize cross-domain planning."),
        ("Principle: Decentralize decision-making", "Push authority to teams where possible."),
        ("Principle: Organize around value", "Value streams not functional silos."),
    ]))

    return dedupe(cards)


def expand_deck(base: list[dict], prefix: str, extras: list[tuple[str, str]]) -> list[dict]:
    cards = list(base)
    for q, ref in extras:
        cards.append(theory(f"{prefix}: {q}", ref))
    return dedupe(cards)


def add_flashcards(cards: list[dict], pairs: list[tuple[str, str]]) -> list[dict]:
    for q, ref in pairs:
        cards.append(theory(q, ref))
    return cards


def build_all() -> dict[str, list[dict]]:
    agile = build_agile()
    scrum = build_scrum()
    kanban = build_kanban()
    safe = build_safe()

    # Expand each deck with cross-reference and drill cards
    agile_extras = [
        ("Когда выбирать Agile подход?", "Высокая неопределённость, нужна частая обратная связь, сложные adaptive problems."),
        ("Когда Agile не лучший выбор?", "Жёсткие регуляторные fixed-scope контракты без возможности iterate — нужна адаптация контракта."),
        ("Contracting for Agile?", "Time & materials + outcome milestones, fixed price per sprint/PI с scope flexibility."),
    ]
    agile = expand_deck(agile, "Agile", agile_extras)

    scrum_extras = [
        ("Scrum Guide 2020: изменение «Development Team»?", "Теперь единая Scrum Team без под-label Developers; акцент на одной команде."),
        ("Accountability vs responsibility в Scrum?", "Accountability — один на роль (PO, SM); work — collective Scrum Team."),
    ]
    scrum = expand_deck(scrum, "Scrum", scrum_extras)

    kanban_extras = [
        ("Kanban cadences?", "Daily Kanban, Replenishment, Delivery Planning, Service Delivery Review, Operations/Strategy reviews."),
        ("Two-tier board?", "Upstream (discovery/options) + downstream (delivery) с разными WIP."),
    ]
    kanban = expand_deck(kanban, "Kanban", kanban_extras)

    safe_extras = [
        ("SAFe principles count?", "10 Lean-Agile principles (e.g. take economic view, apply systems thinking, decentralize decisions)."),
        ("CALMR approach DevOps?", "Culture, Automation, Lean, Measure, Recover — SAFe DevOps competency."),
    ]
    safe = expand_deck(safe, "SAFe", safe_extras)

    # Bulk Q&A pairs for volume
    agile_pairs = [
        ("Что такое burndown chart?", "График оставшейся работы в спринте; trend показывает, успеете ли к goal."),
        ("Что такое burnup chart?", "Done vs total scope; видно scope creep если total растёт."),
        ("Three Amigos?", "PO + dev + tester обсуждают story до sprint — shared understanding."),
        ("Definition of Awesome?", "Расширенная команда vision качества beyond минимального DoD."),
        ("Shu-Ha-Ri в Agile?", "Сначала правила, потом адаптация, потом мастерство — эволюция практик."),
        ("Agile coaching vs consulting?", "Coach развивает capability команды; consultant часто даёт решения."),
        ("System thinking в Agile?", "Оптимизировать whole value stream, не локальный maximum одной команды."),
        ("Flow vs resource efficiency?", "Flow — быстрее ценность клиенту; resource — загрузка людей 100% — often conflict."),
        ("Work in progress aging?", "Старые незавершённые items — signal риска и блокеров."),
        ("Explicit policies пример?", "«Max 3 items в Code Review», «Ready = AC + no blockers»."),
    ]
    scrum_pairs = [
        ("Scrum Master сертификации?", "PSM (Scrum.org), CSM (Scrum Alliance) — знание framework, не замена опыта."),
        ("Product Owner сертификации?", "PSPO, CSPO — ownership и backlog practices."),
        ("Sprint length change?", "Можно между sprints; shorter = faster feedback."),
        ("Carry-over stories?", "Незавершённые возвращаются в PB; анализ причин на retro, не blame."),
        ("Scrum in hardware?", "Possible with longer sprints, physical prototypes as Increment."),
        ("Definition of Done examples?", "Unit tests pass, code review, docs updated, deployed to staging, no critical bugs."),
        ("Sprint zero?", "Controversial — лучше enablers в PB и normal sprints."),
        ("Hardening sprint anti-pattern?", "Quality must be in every Increment."),
        ("Scrum values?", "Commitment, Focus, Openness, Respect, Courage."),
        ("Who orders Product Backlog?", "Product Owner — один ordered list."),
    ]
    kanban_pairs = [
        ("Kanban board electronic tools?", "Jira, Azure Boards, Trello — policies и WIP важнее tool."),
        ("Personal Kanban?", "Individual WIP limits для личной продуктивности."),
        ("Upstream Kanban?", "Discovery/options перед commitment — reduce wrong features."),
        ("Queue replenishment?", "When ready queue < threshold, refill from backlog."),
        ("Triage board?", "Fast classification incoming work by CoS."),
        ("Defect triage policy?", "Separate WIP or class; SLAs by severity."),
        ("Kanban for ops/support?", "Classic: incoming → analyze → fix → verify → done with WIP per tier."),
        ("Metric: percent complete and accurate?", "Forecast quality — % items delivered when promised."),
        ("Policy: unblock first?", "Before new start, resolve blockers on board."),
        ("Fit for purpose?", "Align service policies to customer expectations (David Anderson)."),
    ]
    safe_pairs = [
        ("SAFe implementation roadmap?", "Train leaders → launch ART → expand — incremental not big bang."),
        ("SPC?", "SAFe Program Consultant — certified change agent for SAFe adoption."),
        ("LACE?", "Lean Agile Center of Excellence — coaching and tooling support."),
        ("Value stream mapping in SAFe?", "Identify steps, wait times, automate handoffs on ART."),
        ("Capacity allocation PI?", "Percent capacity for features, enablers, maintenance, innovation."),
        ("Program KPI?", "Predictability measure, PI objectives achievement, flow metrics."),
        ("Predictability Measure?", "Actual business value delivered vs planned PI objectives."),
        ("Compliance in SAFe?", "Built-in quality, documented workflows, approval enablers in backlog."),
        ("Supplier integration?", "Solution train coordinates external vendors on same PI cadence."),
        ("SAFe vs Spotify model?", "SAFe prescriptive; Spotify squads/tribes/chapters — organizational pattern, not full framework."),
    ]

    agile = add_flashcards(agile, agile_pairs)
    scrum = add_flashcards(scrum, scrum_pairs)
    kanban = add_flashcards(kanban, kanban_pairs)
    safe = add_flashcards(safe, safe_pairs)

    return {
        "agile-fundamentals.json": ("Agile — основы", agile),
        "scrum-framework.json": ("Scrum", scrum),
        "kanban-method.json": ("Kanban", kanban),
        "safe-scaled-agile.json": ("SAFe", safe),
    }


def main() -> None:
    decks = build_all()
    out_dir = Path(__file__).parent
    for filename, (name, cards) in decks.items():
        if len(cards) < 100:
            raise SystemExit(f"{filename}: only {len(cards)} cards")
        path = out_dir / filename
        path.write_text(
            json.dumps({"name": name, "cards": cards}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"Written {len(cards)} cards -> {path}")


if __name__ == "__main__":
    main()
