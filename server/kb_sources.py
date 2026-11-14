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


@dataclass(frozen=True)
class KnowledgeSource:
    id: str
    title: str
    homepage: str
    description: str
    match: str  # regex по «id колоды + название + язык»: каким колодам источник подходит
    kind: str  # php_tarball | python_tarball | github
    lang: str = ""  # язык блоков кода по умолчанию
    archive: str = ""
    parts: tuple[GitPart, ...] = ()
    flavor: str = ""  # особенности разметки: mdn, angular, typescript, laravel, node, go


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
    ]
}


def sources_for_deck(deck_id: str, name: str, language: str) -> list[str]:
    hay = f"{deck_id} {name} {language}".lower()
    return [s.id for s in SOURCES.values() if re.search(s.match, hay)]


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


def load_pages(src: KnowledgeSource, say: Progress, tick: Callable[[int, int], None]) -> list[Page]:
    pages: list[Page] = []
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
