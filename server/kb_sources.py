"""Официальные источники базы знаний учебника и их загрузка.

Каждый источник превращается в список страниц `Page` (Markdown), дальше их
режет и индексирует `server.knowledge`. Поддерживаются три способа загрузки:

  * ``php_tarball``    — архив PHP Manual (php.net), «Many HTML files»;
  * ``python_tarball`` — архив HTML-документации docs.python.org;
  * ``github``         — каталоги официальных репозиториев документации
    (MDN на русском, Node.js, TypeScript, Angular, Laravel, Go): одно обращение
    к GitHub API на каталог + скачивание файлов с raw.githubusercontent.com.
"""
from __future__ import annotations

import io
import json
import os
import re
import tarfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from html import unescape
from pathlib import PurePosixPath
from typing import Callable

import requests
from bs4 import BeautifulSoup

from server.knowledge import USER_AGENT, Page, _render, _tidy, parse_php_page, select_php_pages

Progress = Callable[[str], None]


# ── описание источников ─────────────────────────────────────────────


@dataclass(frozen=True)
class GitPart:
    repo: str  # owner/name
    ref: str  # ветка или тег
    path: str = ""  # каталог внутри репозитория
    include: str = r".*"  # regex по относительному пути
    exclude: str = r"(?!)"
    url: Callable[[str, dict], str] = field(default=lambda rel, meta: "", compare=False)
    pick: Callable[[list[str]], list[str]] | None = field(default=None, compare=False)  # доп. отбор файлов


@dataclass(frozen=True)
class WebDoc:
    url: str  # что скачивать (pdf или html)
    title: str
    page_url: str = ""  # куда ведёт сноска (по умолчанию url)
    selector: str = ""  # id корневого элемента html-страницы


@dataclass(frozen=True)
class KnowledgeSource:
    id: str
    title: str
    homepage: str
    description: str
    match: str  # regex по «id колоды + название + язык»: каким колодам источник подходит
    kind: str  # php_tarball | python_tarball | github | web | wikipedia
    lang: str = ""  # язык блоков кода по умолчанию
    archive: str = ""
    parts: tuple[GitPart, ...] = ()
    flavor: str = ""  # особенности разметки: mdn, angular, typescript, laravel, node, go, hugo, mdx
    docs: tuple[WebDoc, ...] = ()


def _strip_ext(rel: str) -> str:
    return re.sub(r"\.(md|html)$", "", rel)


def _angular_url(rel: str, meta: dict) -> str:
    path = _strip_ext(rel)
    path = re.sub(r"/(overview|index)$", "", path)
    return f"https://angular.dev/{path}"


def _go_url(rel: str, meta: dict) -> str:
    path = _strip_ext(rel)
    path = re.sub(r"/index$", "", path)
    return f"https://go.dev/doc/{path}"


PYTHON_LIBRARY = {
    "functions", "stdtypes", "exceptions", "constants", "collections", "collections.abc", "itertools",
    "functools", "operator", "typing", "dataclasses", "enum", "abc", "contextlib", "json", "re", "string",
    "pathlib", "os", "os.path", "sys", "io", "datetime", "time", "logging", "unittest", "unittest.mock",
    "threading", "multiprocessing", "concurrent.futures", "subprocess", "sqlite3", "csv", "argparse",
    "heapq", "bisect", "copy", "pickle", "random", "math", "statistics", "decimal", "inspect", "weakref",
    "hashlib", "secrets", "urllib.parse", "venv", "tkinter", "tkinter.ttk", "queue", "shutil", "glob",
    "tempfile", "textwrap", "timeit", "traceback", "warnings", "doctest", "asyncio", "types", "array",
    "struct", "zipfile", "http.server", "urllib.request", "socket", "selectors", "pdb", "profile", "gc",
}
PYTHON_HOWTO = {"functional", "logging", "regex", "sorting", "descriptor", "enum", "argparse", "annotations"}


def python_selected(rel: str) -> bool:
    parts = rel.split("/")
    if len(parts) != 2 or not parts[1].endswith(".html"):
        return False
    folder, stem = parts[0], parts[1][:-5]
    if folder in ("tutorial", "reference"):
        return True
    if folder == "howto":
        return stem in PYTHON_HOWTO
    if folder == "whatsnew":
        return stem in ("3.10", "3.11", "3.12", "3.13")
    if folder == "library":
        return stem in PYTHON_LIBRARY or stem.startswith("asyncio")
    return False


SOURCES: dict[str, KnowledgeSource] = {
    s.id: s
    for s in [
        KnowledgeSource(
            id="php_manual_ru",
            title="PHP Manual — официальная документация (рус.)",
            homepage="https://www.php.net/manual/ru/",
            description="Справочник языка, нововведения PHP 7–8, массивы, строки, JSON, PDO, дата/время, SPL и др.",
            match=r"php|laravel",
            kind="php_tarball",
            lang="php",
            archive="https://www.php.net/distributions/manual/php_manual_ru.tar.gz",
        ),
        KnowledgeSource(
            id="laravel_docs",
            title="Laravel 12.x — официальная документация",
            homepage="https://laravel.com/docs/12.x",
            description="Маршрутизация, контроллеры, Eloquent, миграции, очереди, кеш, события, тестирование, Sanctum.",
            match=r"laravel|pro-php|php-разработчик",
            kind="github",
            lang="php",
            flavor="laravel",
            parts=(
                GitPart(
                    "laravel/docs", "12.x",
                    include=r"^[\w-]+\.md$",
                    exclude=r"^(readme|license|documentation|contributions)\.md$",
                    url=lambda rel, meta: f"https://laravel.com/docs/12.x/{_strip_ext(rel)}",
                ),
            ),
        ),
        KnowledgeSource(
            id="python_docs",
            title="Python 3.13 — официальная документация",
            homepage="https://docs.python.org/3.13/",
            description="Учебник, справочник языка, встроенные типы и функции, ключевые модули стандартной библиотеки, asyncio.",
            match=r"python|pytorch|ttk|tkinter|pro-ai-trainer|pro-fde|pro-llm-evaluator",
            kind="python_tarball",
            lang="python",
            archive="https://docs.python.org/3.13/archives/python-3.13-docs-html.tar.bz2",
        ),
        KnowledgeSource(
            id="django_docs",
            title="Django — учебник и ORM",
            homepage="https://docs.djangoproject.com/en/5.2/",
            description="Проект и приложения, URL, views, модели, формы и тестирование.",
            match=r"django|python-разработчик|pro-python",
            kind="web", lang="python",
            docs=tuple(WebDoc(f"https://docs.djangoproject.com/en/5.2/intro/tutorial0{i}/", f"Django tutorial: часть {i}") for i in range(1, 6)),
        ),
        KnowledgeSource(
            id="flask_docs",
            title="Flask — официальное руководство",
            homepage="https://flask.palletsprojects.com/en/stable/",
            description="Маршруты, шаблоны, фабрика приложения, blueprints и тесты.",
            match=r"flask|python-разработчик|pro-python",
            kind="web", lang="python",
            docs=tuple(WebDoc(f"https://flask.palletsprojects.com/en/stable/{path}/", f"Flask: {title}")
                       for path, title in (("quickstart", "начало работы"), ("patterns/appfactories", "фабрики приложений"),
                                           ("blueprints", "blueprints"), ("testing", "тестирование"))),
        ),
        KnowledgeSource(
            id="fastapi_docs",
            title="FastAPI — схемы, зависимости и тесты",
            homepage="https://fastapi.tiangolo.com/",
            description="Pydantic, параметры запросов, зависимости, lifespan и TestClient.",
            match=r"fastapi|python-разработчик|pro-python",
            kind="web", lang="python",
            docs=tuple(WebDoc(f"https://fastapi.tiangolo.com/{path}/", f"FastAPI: {title}")
                       for path, title in (("tutorial/body", "тело запроса"), ("tutorial/dependencies", "зависимости"),
                                           ("tutorial/testing", "тестирование"), ("advanced/events", "lifespan"))),
        ),
        KnowledgeSource(
            id="python_data_docs",
            title="NumPy, pandas и matplotlib — работа с данными",
            homepage="https://pandas.pydata.org/docs/getting_started/intro_tutorials/",
            description="Массивы, DataFrame, чтение таблиц, выборки, статистики, объединения и графики.",
            match=r"pandas|numpy|matplotlib|python-разработчик|pro-python",
            kind="web", lang="python",
            docs=(WebDoc("https://numpy.org/doc/stable/user/absolute_beginners.html", "NumPy для начинающих"),
                  WebDoc("https://matplotlib.org/stable/users/explain/quick_start.html", "matplotlib: первые графики"),
                  *(WebDoc(f"https://pandas.pydata.org/docs/getting_started/intro_tutorials/{page}.html", f"pandas: {title}")
                    for page, title in (("02_read_write", "чтение и запись"), ("03_subset_data", "выбор данных"),
                                        ("05_add_columns", "новые столбцы"), ("06_calculate_statistics", "статистики"),
                                        ("08_combine_dataframes", "объединение таблиц")))),
        ),
        KnowledgeSource(
            id="sklearn_basics",
            title="scikit-learn — первые модели и оценка качества",
            homepage="https://scikit-learn.org/stable/getting_started.html",
            description="Обучение, preprocessing, Pipeline, кросс-валидация и предотвращение утечек данных.",
            match=r"scikit|sklearn|python-разработчик|pro-python|pytorch",
            kind="web", lang="python",
            docs=(WebDoc("https://scikit-learn.org/stable/getting_started.html", "scikit-learn: начало работы"),
                  WebDoc("https://scikit-learn.org/stable/common_pitfalls.html", "scikit-learn: утечки данных и типичные ошибки")),
        ),
        KnowledgeSource(
            id="pytorch_basics",
            title="PyTorch — Learn the Basics",
            homepage="https://docs.pytorch.org/tutorials/beginner/basics/intro.html",
            description="Тензоры, Dataset/DataLoader, построение модели, autograd, обучение и сохранение весов.",
            match=r"pytorch|python-разработчик|pro-python|ai-тренер|ai-trainer",
            kind="web", lang="python",
            docs=tuple(WebDoc(f"https://docs.pytorch.org/tutorials/beginner/basics/{page}_tutorial.html", f"PyTorch: {title}")
                       for page, title in (("quickstart", "полный цикл"), ("tensorqs", "тензоры"),
                                           ("data", "данные"), ("buildmodel", "модель"), ("autogradqs", "градиенты"),
                                           ("optimization", "обучение"), ("saveloadrun", "сохранение и загрузка"))),
        ),
        KnowledgeSource(
            id="mdn_js_ru",
            title="MDN Web Docs — JavaScript (рус.)",
            homepage="https://developer.mozilla.org/ru/docs/Web/JavaScript",
            description="Руководство и справочник JavaScript на русском: типы, объекты, промисы, классы, модули, встроенные объекты.",
            match=r"javascript|\bjs\b|node|typescript|angular",
            kind="github",
            lang="js",
            flavor="mdn",
            parts=(
                GitPart(
                    "mdn/translated-content", "main", "files/ru/web/javascript",
                    include=r"\.md$",
                    url=lambda rel, meta: "https://developer.mozilla.org/ru/docs/" + (meta.get("slug") or "Web/JavaScript"),
                ),
            ),
        ),
        KnowledgeSource(
            id="nodejs_api",
            title="Node.js v22 — документация API",
            homepage="https://nodejs.org/docs/latest-v22.x/api/",
            description="Модули Node.js: fs, http, events, stream, worker_threads, process, crypto, ESM/CommonJS, test runner.",
            match=r"node",
            kind="github",
            lang="js",
            flavor="node",
            parts=(
                GitPart(
                    "nodejs/node", "v22.x", "doc/api",
                    include=r"^[\w_-]+\.md$",
                    exclude=r"^(index|all|documentation|synopsis)\.md$",
                    url=lambda rel, meta: f"https://nodejs.org/docs/latest-v22.x/api/{_strip_ext(rel)}.html",
                ),
            ),
        ),
        KnowledgeSource(
            id="typescript_handbook",
            title="TypeScript Handbook — официальная документация",
            homepage="https://www.typescriptlang.org/docs/",
            description="Handbook, справочник типов, модули, tsconfig, файлы деклараций, нововведения TypeScript 5.",
            match=r"typescript|angular|node",
            kind="github",
            lang="ts",
            flavor="typescript",
            parts=(
                GitPart(
                    "microsoft/TypeScript-Website", "v2", "packages/documentation/copy/en",
                    include=r"^(handbook-v2|reference|declaration-files|project-config|modules-reference|get-started|javascript)/.+\.md$"
                    r"|^release-notes/TypeScript 5\.\d+\.md$",
                    url=lambda rel, meta: "https://www.typescriptlang.org" + (meta.get("permalink") or "/docs/"),
                ),
            ),
        ),
        KnowledgeSource(
            id="angular_docs",
            title="Angular — официальная документация (angular.dev)",
            homepage="https://angular.dev/overview",
            description="Компоненты, шаблоны, сигналы, DI, маршрутизация, формы, HttpClient, тестирование, SSR, лучшие практики.",
            match=r"angular",
            kind="github",
            lang="ts",
            flavor="angular",
            parts=(
                GitPart(
                    "angular/angular", "main", "adev/src/content",
                    include=r"^(guide|best-practices|introduction|tools|ecosystem)/.+\.md$",
                    url=_angular_url,
                ),
            ),
        ),
        KnowledgeSource(
            id="go_docs",
            title="Go — официальная документация (go.dev)",
            homepage="https://go.dev/doc/",
            description="Спецификация языка, модель памяти, Effective Go, FAQ, руководства, модули, работа с БД, нововведения Go 1.18+.",
            match=r"\bgo\b|golang|pro-go",
            kind="github",
            lang="go",
            flavor="go",
            parts=(
                GitPart(
                    "golang/go", "master", "doc",
                    include=r"^go_(spec|mem)\.html$",
                    url=lambda rel, meta: "https://go.dev/ref/" + ("spec" if "spec" in rel else "mem"),
                ),
                GitPart(
                    "golang/website", "master", "_content/doc",
                    include=r"\.(md|html)$",
                    exclude=r"^(devel|gopher|install)/|^go1(\.\d|\.1[0-7])?\.(md|html)$|^(contribute|install|asm)\b",
                    url=_go_url,
                ),
            ),
        ),
        KnowledgeSource(
            id="agile_guides",
            title="Scrum Guide, Kanban Guide, Agile-манифест",
            homepage="https://scrumguides.org/",
            description="Официальное руководство по Scrum 2020 (рус.), Agile-манифест и его принципы (рус.), Kanban Guide 2020.",
            match=r"agile|scrum|kanban|канбан|safe",
            kind="web",
            docs=(
                WebDoc("https://scrumguides.org/docs/scrumguide/v2020/2020-Scrum-Guide-Russian.pdf",
                       "Руководство по Скраму 2020"),
                WebDoc("https://agilemanifesto.org/iso/ru/manifesto.html", "Манифест гибкой разработки ПО"),
                WebDoc("https://agilemanifesto.org/iso/ru/principles.html", "Принципы Agile-манифеста"),
                WebDoc("https://kanbanguides.org/english/", "The Kanban Guide"),
            ),
        ),
        KnowledgeSource(
            id="kubernetes_ru",
            title="Kubernetes — документация (рус.)",
            homepage="https://kubernetes.io/ru/docs/",
            description="Русский перевод документации Kubernetes: концепции, объекты, сеть, хранилище, руководства.",
            match=r"devops|kubernetes|k8s",
            kind="github",
            lang="yaml",
            flavor="hugo",
            parts=(
                GitPart(
                    "kubernetes/website", "main", "content/ru/docs",
                    include=r"^(concepts|tasks|tutorials|setup|reference/glossary)/.+\.md$|^reference/[\w-]+\.md$",
                    url=lambda rel, meta: "https://kubernetes.io/ru/docs/" + re.sub(r"(/?_index)?\.md$", "/", rel),
                ),
            ),
        ),
        KnowledgeSource(
            id="docker_docs",
            title="Docker — официальная документация",
            homepage="https://docs.docker.com/",
            description="Сборка образов и кеш, Dockerfile, Compose, сети, тома, безопасность Docker Engine.",
            match=r"devops|docker|pro-fde|forward deployed",
            kind="github",
            lang="dockerfile",
            flavor="hugo",
            parts=(
                GitPart(
                    "docker/docs", "main", "content/manuals",
                    include=r"^(build/(building|cache|concepts|bake|building)|compose/(how-tos|intro|gettingstarted)"
                    r"|engine/(storage|network|containers|security|logging|daemon))/.*\.md$|^compose/_index\.md$",
                    url=lambda rel, meta: "https://docs.docker.com/" + re.sub(r"(/?_index)?\.md$", "/", rel),
                ),
            ),
        ),
        KnowledgeSource(
            id="prompting_guide",
            title="Prompt Engineering Guide (promptingguide.ai)",
            homepage="https://www.promptingguide.ai/ru",
            description="Техники промптинга, RAG, агенты, риски и prompt injection; русский перевод там, где он есть.",
            match=r"prompt|промпт|llm|ai-trainer|ai-тренер|pro-fde|forward deployed|ai-artist|нейрокреатор",
            kind="github",
            lang="",
            flavor="mdx",
            parts=(
                GitPart(
                    "dair-ai/Prompt-Engineering-Guide", "main", "pages",
                    include=r"^(introduction|techniques|applications|risks|agents|guides|research)(/.+)?\.(ru|en)\.mdx$",
                    url=lambda rel, meta: "https://www.promptingguide.ai/" + ("ru/" if ".ru." in rel else "")
                    + re.sub(r"\.(ru|en)\.mdx$", "", rel),
                    pick=lambda rels: [
                        r for r in rels if ".ru." in r or r.replace(".en.mdx", ".ru.mdx") not in set(rels)
                    ],
                ),
            ),
        ),
        KnowledgeSource(
            id="hf_trl",
            title="Hugging Face TRL — дообучение LLM",
            homepage="https://huggingface.co/docs/trl",
            description="SFT, DPO, GRPO, reward-модели, PEFT/LoRA, chat templates — документация библиотеки TRL.",
            match=r"ai-trainer|ai-тренер|pytorch",
            kind="github",
            lang="python",
            flavor="mdx",
            parts=(
                GitPart(
                    "huggingface/trl", "main", "docs/source",
                    include=r"^[\w-]+\.md$",
                    exclude=r"^(index|installation|community_tutorials|clis|.*(amd|trainium|vllm|deepspeed|jobs).*)\.md$",
                    url=lambda rel, meta: f"https://huggingface.co/docs/trl/{_strip_ext(rel)}",
                ),
            ),
        ),
        KnowledgeSource(
            id="hf_diffusers",
            title="Hugging Face Diffusers — генерация изображений",
            homepage="https://huggingface.co/docs/diffusers",
            description="Диффузионные пайплайны, сэмплеры, ControlNet, IP-Adapter, inpainting, LoRA-обучение, оптимизация.",
            match=r"ai-artist|нейрокреатор",
            kind="github",
            lang="python",
            flavor="mdx",
            parts=(
                GitPart(
                    "huggingface/diffusers", "main", "docs/source/en",
                    include=r"^(using-diffusers|training|conceptual|tutorials|optimization)/.+\.md$|^(quicktour|stable_diffusion)\.md$",
                    url=lambda rel, meta: f"https://huggingface.co/docs/diffusers/{_strip_ext(rel)}",
                ),
            ),
        ),
        KnowledgeSource(
            id="wikipedia_ru",
            title="Википедия (рус.) — статьи по темам колод",
            homepage="https://ru.wikipedia.org/",
            description="Статьи русской Википедии, подобранные поиском по каждой теме каждой колоды (CC BY-SA).",
            match=r".",
            kind="wikipedia",
        ),
    ]
}


def sources_for_deck(deck_id: str, name: str, language: str) -> list[str]:
    hay = f"{deck_id} {name} {language}".lower()
    return [s.id for s in SOURCES.values() if re.search(s.match, hay)]


def deck_subject(name: str) -> str:
    """«Go-разработчик — теория» → «Go программирование»: предмет колоды для поиска."""
    s = re.sub(r"\s+[—-]\s+(теория|практикум|основы|код)\b.*$", "", name, flags=re.I)
    s = re.sub(r"\b(live-coding|\(полная\))", "", s, flags=re.I)
    s = re.sub(r"-разработчик\b", " программирование", s)
    s = re.sub(r"-инженер\b", "", s)
    return " ".join(s.replace("/", " ").split())


# ── загрузка ─────────────────────────────────────────────────────────


def _get(url: str, *, timeout: int = 120, api: bool = False) -> requests.Response:
    headers = {"User-Agent": USER_AGENT}
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if api and token:
        headers["Authorization"] = f"Bearer {token}"
    r = requests.get(url, headers=headers, timeout=timeout)
    if api and r.status_code == 403 and "rate limit" in r.text.lower():
        raise RuntimeError("GitHub API: превышен лимит запросов (60/час без токена). Повторите позже или задайте GITHUB_TOKEN.")
    r.raise_for_status()
    return r


def fetch_github_part(part: GitPart, say: Progress) -> dict[str, str]:
    tree_ref = f"{part.ref}:{part.path}" if part.path else part.ref
    data = _get(f"https://api.github.com/repos/{part.repo}/git/trees/{tree_ref}?recursive=1", api=True).json()
    inc, exc = re.compile(part.include), re.compile(part.exclude)
    rels = [
        x["path"] for x in data.get("tree", [])
        if x.get("type") == "blob" and inc.search(x["path"]) and not exc.search(x["path"])
    ]
    if part.pick:
        rels = part.pick(rels)
    say(f"{part.repo}: файлов к загрузке — {len(rels)}")
    base = f"https://raw.githubusercontent.com/{part.repo}/{part.ref}/" + (part.path + "/" if part.path else "")

    def one(rel: str) -> tuple[str, str | None]:
        from urllib.parse import quote

        for attempt in range(3):
            try:
                return rel, _get(base + quote(rel), timeout=60).text
            except requests.RequestException:
                if attempt == 2:
                    return rel, None
        return rel, None

    out: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=8) as pool:
        for rel, text in pool.map(one, rels):
            if text is not None:
                out[rel] = text
    return out


def _tar_files(url: str, mode: str, keep: Callable[[str], bool], *, flat: bool) -> dict[str, str]:
    r = _get(url, timeout=600)
    files: dict[str, str] = {}
    with tarfile.open(fileobj=io.BytesIO(r.content), mode=mode) as tar:
        for m in tar.getmembers():
            if not m.isfile() or not m.name.endswith(".html"):
                continue
            rel = PurePosixPath(m.name).name if flat else "/".join(PurePosixPath(m.name).parts[1:])
            if not keep(rel):
                continue
            f = tar.extractfile(m)
            if f:
                files[rel] = f.read().decode("utf-8", "replace")
    return files


def load_pages(
    src: KnowledgeSource, say: Progress, tick: Callable[[int, int], None], context: dict | None = None
) -> list[Page]:
    """context["decks"] — [{"name", "topics": [...]}, ...]: нужен источнику wikipedia для подбора статей."""
    pages: list[Page] = []
    if src.kind == "web":
        for i, doc in enumerate(src.docs, 1):
            say(f"Скачиваю {doc.url}")
            page = fetch_web_doc(doc)
            if page:
                pages.append(page)
            tick(i, len(src.docs))
        return pages
    if src.kind == "wikipedia":
        return load_wikipedia(((context or {}).get("decks") or []), say, tick)
    if src.kind == "php_tarball":
        say(f"Скачиваю {src.archive}")
        files = _tar_files(src.archive, "r:gz", lambda rel: True, flat=True)
        names = select_php_pages(files)
        say(f"В архиве {len(files)} страниц, отобрано {len(names)}")
        for i, name in enumerate(names, 1):
            page = parse_php_page(name, files[name], src.homepage)
            if page:
                pages.append(page)
            tick(i, len(names))
        return pages
    if src.kind == "python_tarball":
        say(f"Скачиваю {src.archive}")
        files = _tar_files(src.archive, "r:bz2", python_selected, flat=False)
        say(f"Отобрано страниц: {len(files)}")
        for i, rel in enumerate(sorted(files), 1):
            page = parse_sphinx_page(rel, files[rel], src.homepage + rel)
            if page:
                pages.append(page)
            tick(i, len(files))
        return pages
    if src.kind == "github":
        for part in src.parts:
            files = fetch_github_part(part, say)
            for i, rel in enumerate(sorted(files), 1):
                page = parse_doc_file(src, part, rel, files[rel])
                if page:
                    pages.append(page)
                tick(i, len(files))
        return pages
    raise ValueError(f"Неизвестный тип источника: {src.kind}")


# ── разбор: Sphinx HTML (docs.python.org) ───────────────────────────


def parse_sphinx_page(rel: str, html: str, url: str) -> Page | None:
    soup = BeautifulSoup(html, "html.parser")
    root = soup.find(attrs={"role": "main"}) or soup.find(class_="body") or soup.body
    if root is None:
        return None
    h1 = root.find("h1")
    title = " ".join(h1.get_text(" ").replace("¶", "").split()) if h1 else rel
    out: list[str] = []
    _render(root, out, "python")
    md = _tidy("".join(out)).replace("¶", "")
    if len(md) < 80:
        return None
    return Page(name=rel, title=title, url=url, markdown=md)


# ── разбор: Markdown / HTML-фрагменты из репозиториев ───────────────

_FRONT = re.compile(r"\A---\s*\n([\s\S]*?)\n---\s*\n")
_GO_META = re.compile(r"\A\s*<!--\s*(\{[\s\S]*?\})\s*-->")
_FENCE = re.compile(r"(```[\s\S]*?```|~~~[\s\S]*?~~~)")
_HTML_TAG = re.compile(
    r"</?(?:a|div|span|p|br|img|code|kbd|sup|sub|em|strong|b|i|u|table|tr|td|th|thead|tbody|ul|ol|li|section|details|"
    r"summary|figure|figcaption|iframe|video|source|hr|dl|dt|dd|h[1-6]|small|var|abbr|picture|blockquote|"
    r"docs-[\w-]+|nav|aside|header|footer|main|article)\b[^<>]*?/?>",
    re.I,
)
_MDN_KEEP = {"jsxref", "glossary", "domxref", "htmlelement", "cssxref", "httpheader", "httpmethod", "httpstatus",
             "jsxref", "link", "rfc", "svgelement", "event", "jsfunc", "experimental_inline"}


def _front_matter(text: str) -> tuple[dict, str]:
    m = _FRONT.match(text)
    if not m:
        return {}, text
    meta = {}
    for line in m.group(1).splitlines():
        kv = re.match(r"^(\w[\w-]*):\s*(.*)$", line)
        if kv:
            meta[kv.group(1)] = kv.group(2).strip().strip("'\"")
    return meta, text[m.end():]


def _mdn_macro(m: re.Match) -> str:
    name = m.group(1).lower()
    args = re.findall(r'"([^"]*)"|\'([^\']*)\'', m.group(2) or "")
    vals = [a or b for a, b in args]
    if name not in _MDN_KEEP or not vals:
        return ""
    text = vals[1] if len(vals) > 1 and vals[1] else vals[0].split("/")[-1]
    return f"`{text}`" if name in ("jsxref", "domxref", "htmlelement", "cssxref", "httpheader", "jsfunc") else text


def _clean_code(code: str, flavor: str) -> str:
    head, _, body = code.partition("\n")
    info = head.strip("`~ \t").split()
    lang = info[0].lower() if info else ""
    lang = {"javascript": "js", "typescript": "ts", "shell": "bash", "sh": "bash", "console": "bash"}.get(lang, lang)
    lines = body.rsplit("\n", 1)[0].split("\n") if body.rstrip().endswith(("```", "~~~")) else body.split("\n")
    if flavor == "typescript":
        lines = [ln for ln in lines if not re.match(r"^\s*//\s*(@\w+|\^\?|\s*\^)", ln) and ln.strip() != "// ---cut---"]
    return f"```{lang}\n" + "\n".join(lines).strip("\n") + "\n```"


def _clean_prose(text: str, flavor: str) -> str:
    text = re.sub(r"<!--[\s\S]*?-->", "", text)
    if flavor == "hugo":  # шорткоды Hugo: {{< glossary_tooltip text="Под" ... >}}, {{< note >}}
        text = re.sub(r"\{\{[<%][^{}]*?\btext=\"([^\"]+)\"[^{}]*?[>%]\}\}", r"\1", text)
        text = re.sub(r"\{\{[<%][\s\S]*?[>%]\}\}", "", text)
    if flavor == "mdx":  # импорты и JSX-компоненты (<Callout>, <Tip>, <Screenshot .../>)
        text = re.sub(r"^(import|export)\s.*$", "", text, flags=re.M)
        text = re.sub(r"</?(?:[A-Z][\w.]*|hfoptions?)\b(?:[^<>{}]|\{[^{}]*\})*?/?>", "", text)
        text = re.sub(r"\[\[open-in-colab\]\]", "", text)
    if flavor == "mdn":
        text = re.sub(r"\{\{\s*([\w-]+)\s*(?:\(([^}]*)\))?\s*\}\}", _mdn_macro, text)
    text = re.sub(r"^\s*[-*]\s+\[[^\]]+\]\(#[^)]*\)\s*$", "", text, flags=re.M)  # оглавления
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)  # картинки
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)  # ссылки → текст
    text = re.sub(r"\[([^\]]+)\]\[[^\]]*\]", r"\1", text)
    text = re.sub(r"^\[[^\]]+\]:\s*\S+.*$", "", text, flags=re.M)  # определения ссылок
    text = re.sub(r"^>\s*\[!(\w+)\]\s*$", r"> \1:", text, flags=re.M)
    text = re.sub(r"^(?:TIP|NOTE|IMPORTANT|HELPFUL|CRITICAL|QUESTION|SUMMARY|TLDR|WARNING): ", "", text, flags=re.M)
    text = _HTML_TAG.sub("", text)
    text = re.sub(r"[ \t]*\{[#.][\w.-]+\}", "", text)  # явные якоря заголовков
    text = re.sub(r"^[ \t]*(#{1,6})[ \t]+(.+?)[ \t#]*$",
                  lambda m: "\n\n" + "#" * min(4, len(m.group(1)) + 1) + " " + m.group(2) + "\n\n", text, flags=re.M)
    text = unescape(text)
    return re.sub(r"[ \t]+\n", "\n", text)


def _markdown_body(text: str, flavor: str) -> str:
    if flavor == "angular":
        def docs_code(m: re.Match) -> str:
            attrs, body = m.group(1), m.group(2)
            if not body.strip():
                return ""
            lang = re.search(r'language="(\w+)"', attrs)
            return f"\n```{lang.group(1) if lang else 'ts'}\n{unescape(body).strip()}\n```\n"
        text = re.sub(r"<docs-code\b([^>]*)>([\s\S]*?)</docs-code>", docs_code, text)
        text = re.sub(r"<docs-code\b[^>]*/>", "", text)
    parts = _FENCE.split(text)
    out = []
    for i, part in enumerate(parts):
        out.append(_clean_code(part, flavor) if i % 2 == 1 else _clean_prose(part, flavor))
    md = "\n".join(out)
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md.strip()


def _html_fragment(html: str, lang: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    out: list[str] = []
    for node in soup.contents:
        _render(node, out, lang)
    return _tidy("".join(out))


def parse_doc_file(src: KnowledgeSource, part: GitPart, rel: str, text: str) -> Page | None:
    meta: dict = {}
    text = text.lstrip(chr(0xFEFF)).replace(chr(13) + chr(10), chr(10))
    if rel.endswith(".html"):
        m = _GO_META.match(text)
        if m:
            try:
                meta = {k.lower(): v for k, v in json.loads(m.group(1)).items()}
            except ValueError:
                meta = {}
            text = text[m.end():]
        md = _html_fragment(text, src.lang)
    else:
        meta, text = _front_matter(text)
        md = _markdown_body(text, src.flavor)

    title = meta.get("title", "")
    if not title:
        h = re.search(r"^#{2} (.+)$", md, flags=re.M)  # «# Заголовок» после сдвига уровней стал «##»
        if h:
            title = h.group(1).strip()
    if not title:
        h = re.search(r'<docs-decorative-header[^>]*title="([^"]+)"', text)
        title = h.group(1) if h else PurePosixPath(rel).stem.replace("-", " ").replace("_", " ")
    title = re.sub(r"[`*]", "", title).strip()
    if src.flavor == "node":
        title = f"Node.js: {title}"
    elif src.flavor == "laravel":
        title = f"Laravel: {title}"
    elif src.flavor == "angular":
        title = f"Angular: {title}"

    if len(md) < 120:
        return None
    url = part.url(rel, meta) or src.homepage
    return Page(name=f"{part.repo}/{rel}", title=title, url=url, markdown=md)


# ── разбор: отдельные веб-документы (PDF, HTML) ────────────────────


def _paragraphize(text: str) -> str:
    """Склеить строки PDF в абзацы: разрыв — после строки, оканчивающейся точкой/двоеточием."""
    paras: list[str] = []
    buf: list[str] = []
    for raw in text.splitlines():
        line = " ".join(raw.split())
        if not line:
            continue
        if re.fullmatch(r"\d{1,3}", line):  # номер страницы
            continue
        if buf and buf[-1].endswith("-") and line[:1].islower():
            buf[-1] = buf[-1][:-1] + line  # перенос слова
        else:
            buf.append(line)
        if re.search(r"[.:!?»;]$", line) or (len(line) < 60 and not line.endswith(",")):
            paras.append(" ".join(buf))
            buf = []
    if buf:
        paras.append(" ".join(buf))
    out = []
    for p in paras:
        if re.search(r"[\w.+-]+@[\w-]+\.\w+", p) or "......" in p:  # контакты переводчиков, оглавление
            continue
        # короткая строка без точки — вероятно, заголовок раздела
        if len(p) < 70 and not re.search(r"[.,;:!?]$", p) and not p.startswith(("•", "-", "–")):
            out.append(f"### {p}")
        else:
            out.append(p.lstrip("•–- ").strip() if p.startswith(("•", "–")) else p)
    return "\n\n".join(out)


def fetch_web_doc(doc: WebDoc) -> Page | None:
    r = _get(doc.url, timeout=120)
    url = doc.page_url or doc.url
    ctype = r.headers.get("content-type", "")
    if doc.url.lower().endswith(".pdf") or "pdf" in ctype:
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(r.content))
        text = "\n".join((p.extract_text() or "") for p in reader.pages)
        md = _paragraphize(text)
    else:
        soup = BeautifulSoup(r.content, "html.parser")
        for tag in soup(["header", "footer", "nav", "script", "style", "form", "aside"]):
            tag.decompose()
        root = (soup.find(id=doc.selector) if doc.selector else None) or soup.find("main") or soup.find("article") or soup.body
        if root is None:
            return None
        out: list[str] = []
        _render(root, out, "")
        md = _tidy("".join(out))
    if len(md) < 200:
        return None
    return Page(name=doc.url, title=doc.title, url=url, markdown=md)


# ── Википедия: статьи по темам колод ────────────────────────────────

WIKI_API = "https://ru.wikipedia.org/w/api.php"
WIKI_GENERIC = {"основы", "разное", "инструменты", "тестирование", "производительность", "безопасность", "api", "stdlib"}
WIKI_MIN_RATIO = 0.065  # доля слов статьи из словаря колоды (подобрано: «Python» 0.073, «Colt Python» 0.037)
WIKI_TAIL = re.compile(r"\n== (Примечания|Литература|Ссылки|См\. также|Источники|Комментарии) ==[\s\S]*$")


def _wiki(params: dict) -> dict:
    params = {"format": "json", "formatversion": "2", **params}
    for attempt in range(3):
        try:
            r = requests.get(WIKI_API, params=params, headers={"User-Agent": USER_AGENT}, timeout=60)
            if r.status_code == 429:
                import time

                time.sleep(5 * (attempt + 1))
                continue
            r.raise_for_status()
            return r.json()
        except requests.RequestException:
            if attempt == 2:
                raise
    return {}


WIKI_STOP = {
    "который", "которая", "которые", "которых", "чтобы", "когда", "если", "между", "через", "после", "можно",
    "нужно", "только", "также", "может", "этого", "всегда", "часто", "обычно", "например", "where", "which",
    "their", "there", "these", "about", "would", "should", "other", "value", "return", "function",
}


def deck_vocab(texts: list[str], limit: int = 300) -> list[str]:
    """Частые содержательные слова карточек колоды — для отсева нерелевантных статей."""
    counts: dict[str, int] = {}
    for text in texts:
        for w in re.findall(r"[a-zа-яё]{5,}", text.lower()):
            if w not in WIKI_STOP:
                stem = w[:6]
                counts[stem] = counts.get(stem, 0) + 1
    return [w for w, _ in sorted(counts.items(), key=lambda kv: -kv[1])[:limit]]


def wiki_relevance(text: str, vocab: set[str]) -> float:
    words = {w[:6] for w in re.findall(r"[a-zа-яё]{5,}", text[:6000].lower())}
    overlap = len(words & vocab)
    return overlap / len(words) if words and overlap >= 8 else 0.0


def wiki_queries(decks: list[dict]) -> list[tuple[str, str, int, int]]:
    """Поисковые запросы: (запрос, запасной запрос, сколько статей взять).

    Для каждой колоды — её предмет, для каждой темы — «тема + предмет»; если так ничего
    не найдено, ищется тема без предмета (многословные темы, чтобы не брать случайное).
    """
    queries: dict[str, tuple[str, str, int, int]] = {}
    for di, d in enumerate(decks):
        subject = deck_subject(d.get("name", ""))
        if subject:
            queries.setdefault(subject, (subject, "", 3, di))
        for topic in d.get("topics", []):
            t = " ".join(topic.replace("/", " ").split())
            if not t or t.lower() in WIKI_GENERIC:
                continue
            q = f"{t} {subject}".strip()
            queries.setdefault(q, (q, t if len(t.split()) >= 2 or len(t) >= 8 else "", 2, di))
    return list(queries.values())


def load_wikipedia(decks: list[dict], say: Progress, tick: Callable[[int, int], None]) -> list[Page]:
    if not decks:
        raise RuntimeError("нет колод для подбора статей")
    queries = wiki_queries(decks)
    say(f"Поиск статей Википедии: {len(queries)} запросов по темам колод")

    def run(q: str, n: int) -> list[str]:
        try:
            data = _wiki({"action": "query", "list": "search", "srsearch": q, "srlimit": n, "srnamespace": 0})
        except requests.RequestException:
            return []
        return [h["title"] for h in data.get("query", {}).get("search", [])]

    def search(item: tuple[str, str, int, int]) -> list[str]:
        q, fallback, n, _deck = item
        found = run(q, n)
        return found or (run(fallback, 1) if fallback else [])

    vocabs = [set(d.get("vocab") or []) for d in decks]
    owners: dict[str, set[int]] = {}  # статья → колоды, для которых её нашли
    titles: list[str] = []
    with ThreadPoolExecutor(max_workers=3) as pool:
        for i, (item, found) in enumerate(zip(queries, pool.map(search, queries)), 1):
            for t in found:
                if t not in owners:
                    owners[t] = set()
                    titles.append(t)
                owners[t].add(item[3])
            tick(i, len(queries))
    say(f"Найдено статей: {len(titles)}, загружаю тексты")

    def fetch(title: str) -> Page | None:
        try:
            data = _wiki({"action": "query", "prop": "extracts|pageprops", "explaintext": 1,
                          "exsectionformat": "wiki", "redirects": 1, "titles": title})
        except requests.RequestException:
            return None
        pages = data.get("query", {}).get("pages", [])
        if not pages or pages[0].get("missing"):
            return None
        p = pages[0]
        if "disambiguation" in (p.get("pageprops") or {}):
            return None
        text = WIKI_TAIL.sub("", "\n" + (p.get("extract") or "")).strip()
        text = re.sub(r"\{\displaystyle ([^\n]*?)\}", r"$\1$", text)  # формулы
        text = re.sub(r"^(=+) (.+?) =+$", lambda m: "#" * min(4, len(m.group(1))) + " " + m.group(2), text, flags=re.M)
        text = re.sub(r"\n{3,}", "\n\n", text)
        if len(text) < 400:
            return None
        vocab = set().union(*(vocabs[i] for i in owners.get(title, ())))
        if vocab and wiki_relevance(text, vocab) < WIKI_MIN_RATIO:
            return None  # «Colt Python» для колоды по Python и т. п.
        title_ = p.get("title", title)
        url = "https://ru.wikipedia.org/wiki/" + requests.utils.quote(title_.replace(" ", "_"))
        return Page(name=f"wiki:{title_}", title=title_, url=url, markdown=text)

    out: list[Page] = []
    with ThreadPoolExecutor(max_workers=3) as pool:
        for i, page in enumerate(pool.map(fetch, titles), 1):
            if page:
                out.append(page)
            tick(i, len(titles))
    say(f"Релевантных статей: {len(out)} из {len(titles)}")
    return out
