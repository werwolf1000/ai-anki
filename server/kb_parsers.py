"""Парсеры официальной документации Python-профессии (без сетевых запросов).

У каждого сайта свой выбор статьи и очистка служебных элементов. Общий рендерер
сохраняет структуру, код, таблицы и ссылки для последующего разбиения на RAG-чанки.
Не подменяем отсутствующую статью всем body: изменение шаблона должно быть заметно.
"""
from __future__ import annotations

import re
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup, Comment, NavigableString, Tag

from server.knowledge import Page


class DocumentationParseError(ValueError):
    """Страница не соответствует ожидаемому шаблону документации."""


_CHROME = (
    "script, style, nav, header, footer, aside, form, button, input, svg, iframe, noscript, "
    ".headerlink, .viewcode-link, .copybtn, .linenos, .linenodiv, "
    ".sidebar, .sphinxsidebar, .related, .toctree-wrapper, .contents.local, "
    ".prev-next-area, .bd-header-article, .bd-footer-article, .edit-this-page"
)
_GALLERY = ".sphx-glr-footer, .sphx-glr-download-link-note, .sphx-glr-timing, .sphx-glr-signature"
_BLOCKS = {"p", "div", "section", "article", "main", "blockquote", "dl", "dd", "figure", "figcaption", "details"}


def _remove(root: Tag, selectors: str) -> None:
    for tag in root.select(selectors):
        if tag.parent is not None:  # родитель мог быть удалён предыдущим селектором
            tag.decompose()


def _language(pre: Tag) -> str:
    nodes = [pre, *list(pre.parents)[:3]]
    code = pre.find("code")
    if code is not None:
        nodes.insert(0, code)
    for node in nodes:
        if "sphx-glr-script-out" in (node.get("class") or []):
            return "text"
    for node in nodes:
        for cls in node.get("class") or []:
            match = re.fullmatch(r"(?:language|highlight)-([\w+-]+)", cls, re.I)
            if match:
                lang = match[1].lower()
                if lang in {"default", "ipython", "ipython3", "python", "pycon", "python3"}:
                    return "pycon" if re.search(r"(?m)^\s*(>>>|In \[\d+\]:)", pre.get_text()) else "python"
                return {"none": "text", "py": "python", "sh": "bash"}.get(lang, lang)
    return "pycon" if re.search(r"(?m)^\s*(>>>|In \[\d+\]:)", pre.get_text()) else "python"


def _link(href: str, base: str) -> str:
    absolute = urljoin(base, href)
    return absolute if urlsplit(absolute).scheme in {"http", "https"} else ""


def _table(node: Tag, base: str) -> str:
    """Сохраняем заголовки и строки DataFrame/API-таблиц, включая индекс."""
    rows = []
    header = False
    for tr in node.find_all("tr"):
        cells = tr.find_all(["th", "td"], recursive=False)
        if not cells:
            continue
        if not rows:
            header = any(cell.name == "th" for cell in cells)
        rows.append([re.sub(r"\s+", " ", _children(cell, base)).strip().replace("|", "\\|") for cell in cells])
    if not rows:
        return ""
    width = max(map(len, rows))
    if not header:
        rows.insert(0, [""] * width)
    lines = ["| " + " | ".join(row + [""] * (width - len(row))) + " |" for row in rows]
    lines.insert(1, "| " + " | ".join(["---"] * width) + " |")
    caption = node.find("caption")
    title = _children(caption, base).strip() + "\n\n" if caption else ""
    return "\n\n" + title + "\n".join(lines) + "\n\n"


def _children(node: Tag, base: str) -> str:
    return "".join(_render(child, base) for child in node.children)


def _render(node, base: str) -> str:
    if isinstance(node, Comment):
        return ""
    if isinstance(node, NavigableString):
        return re.sub(r"\s+", " ", str(node))
    if not isinstance(node, Tag):
        return ""
    name = node.name
    if name == "pre":
        code = node.get_text().strip("\n\r")
        return f"\n\n```{_language(node)}\n{code}\n```\n\n" if code.strip() else ""
    if name == "table":
        return _table(node, base)
    if name == "code":
        return "`" + node.get_text().strip() + "`"
    if name in {"h1", "h2", "h3", "h4", "h5", "h6"}:
        title = " ".join(node.get_text(" ").split())
        return "\n\n" + "#" * min(4, max(2, int(name[1]))) + " " + title + "\n\n"
    if name == "a":
        label = _children(node, base).strip()
        href = _link(node.get("href", ""), base) if node.get("href") else ""
        return f"[{label}]({href})" if href and label else label
    if name == "img":
        # Иллюстрации не индексируем как изображения; оставляем смысловую подпись.
        return " " + node.get("alt", "").strip() + " "
    if name == "br":
        return "\n"
    if name == "li":
        return "\n- " + _children(node, base).strip() + "\n"
    if name in {"ul", "ol"}:
        return "\n\n" + _children(node, base).strip() + "\n\n"
    if name in {"dt", "summary"}:
        return "\n\n" + _children(node, base).strip() + "\n\n"
    text = _children(node, base)
    return "\n\n" + text.strip() + "\n\n" if name in _BLOCKS else text


def _page(html: str | bytes, url: str, title: str, *, site: str,
          roots: tuple[str, ...], remove: str = "", prepare=None) -> Page:
    soup = BeautifulSoup(html, "html.parser")
    root = None
    for selector in roots:
        root = soup.select_one(selector)
        if root is not None:
            break
    if root is None:
        raise DocumentationParseError(f"{site}: не найдена статья ({url})")
    _remove(root, _CHROME + (", " + remove if remove else ""))
    for anchor in root.select(".toc-backref"):
        anchor.unwrap()
    if prepare is not None:
        prepare(root)
    heading = root.find("h1")
    if heading is None:
        raise DocumentationParseError(f"{site}: отсутствует заголовок статьи ({url})")
    title = f"{site}: {' '.join(heading.get_text(' ').split())}"
    raw = _render(root, url)
    # Пробелы/пустые строки нормализуем только вне кода.
    parts = re.split(r"(```[\s\S]*?```)", raw)
    for i in range(0, len(parts), 2):
        parts[i] = re.sub(r"[ \t]+\n", "\n", parts[i])
        parts[i] = re.sub(r"\n[ \t]+", "\n", parts[i])
        parts[i] = re.sub(r"\n{3,}", "\n\n", parts[i])
    markdown = "".join(parts).strip()
    if len(markdown) < 200:
        raise DocumentationParseError(f"{site}: статья слишком короткая ({url})")
    return Page(name=url, title=title, url=url, markdown=markdown)


def parse_django(html: str | bytes, url: str, title: str = "") -> Page:
    return _page(html, url, title, site="Django", roots=("#docs-content",),
                 remove=".breadcrumbs, .copybutton, .c-tabs-nav, .c-tabs-navigation")


def parse_flask(html: str | bytes, url: str, title: str = "") -> Page:
    return _page(html, url, title, site="Flask", roots=('div.body[role="main"]', "article.bd-article"),
                 remove=".clearer, .sphinx-tabs-tab")


def _fastapi_tabs(root: Tag) -> None:
    for details in root.find_all("details"):
        summary = details.find("summary", recursive=False)
        if summary is not None and summary.get_text(" ", strip=True) == "AI coding agents":
            details.decompose()  # повторяющаяся промо-вставка, не содержание урока
    # Варианты Python/Pydantic остаются вместе со своими подписями, в том числе
    # скрытые CSS вкладки. Иначе пример легко отнести к неверной версии API.
    for tabs in root.select(".tabbed-set"):
        labels = tabs.select(":scope > .tabbed-labels label")
        panels = tabs.select(":scope > .tabbed-content > .tabbed-block")
        for label, panel in zip(labels, panels):
            heading = BeautifulSoup("<h4></h4>", "html.parser").h4
            heading.string = label.get_text(" ", strip=True)
            panel.insert(0, heading)
        _remove(tabs, ".tabbed-labels")


def parse_fastapi(html: str | bytes, url: str, title: str = "") -> Page:
    return _page(html, url, title, site="FastAPI", roots=("article.md-content__inner",),
                 remove=".md-content__button, .md-source-file, .md-feedback, .md-typeset__scrollwrap > .md-clipboard",
                 prepare=_fastapi_tabs)


def parse_numpy(html: str | bytes, url: str, title: str = "") -> Page:
    return _page(html, url, title, site="NumPy", roots=("article.bd-article", 'div.body[role="main"]'),
                 remove=".version-switcher__container, .sd-tab-label")


def parse_pandas(html: str | bytes, url: str, title: str = "") -> Page:
    return _page(html, url, title, site="pandas", roots=("article.bd-article",),
                 remove=".pandas-navbar, .ipython-prompt")


def parse_matplotlib(html: str | bytes, url: str, title: str = "") -> Page:
    return _page(html, url, title, site="matplotlib", roots=("article.bd-article", 'div.body[role="main"]'),
                 remove=_GALLERY)


def _sklearn_estimators(root: Tag) -> None:
    # sklearn показывает и HTML-диаграмму estimator, и текстовую копию.
    # Для RAG оставляем один repr с параметрами вместо кнопок/дублирования.
    for wrapper in root.select(".sk-top-container"):
        fallback = wrapper.select_one(".sk-text-repr-fallback")
        if fallback is not None:
            wrapper.replace_with(fallback.extract())
        else:
            _remove(wrapper, ".sk-estimator-doc-link, .sk-toggleable__label-arrow")


def parse_sklearn(html: str | bytes, url: str, title: str = "") -> Page:
    return _page(html, url, title, site="scikit-learn", roots=("article.bd-article", 'div.body[role="main"]'),
                 remove=_GALLERY, prepare=_sklearn_estimators)


def parse_pytorch(html: str | bytes, url: str, title: str = "") -> Page:
    return _page(html, url, title, site="PyTorch", roots=("#pytorch-article article.bd-article", "article.bd-article", ".pytorch-article"),
                 remove=_GALLERY + ", .pytorch-call-to-action-links, .tutorials-callout, .sphx-glr-binder, p.sphx-glr-example-title, .date-info-last-verified")


def parse_sqlalchemy(html: str | bytes, url: str, title: str = "") -> Page:
    return _page(html, url, title, site="SQLAlchemy", roots=('#docs-body[role="main"]',),
                 remove=".docs-navigation, .top, .sql-link")


PARSERS = {
    "django": parse_django, "flask": parse_flask, "fastapi": parse_fastapi,
    "numpy": parse_numpy, "pandas": parse_pandas, "matplotlib": parse_matplotlib,
    "sklearn": parse_sklearn, "pytorch": parse_pytorch, "sqlalchemy": parse_sqlalchemy,
}


def parse_document(parser: str, html: str | bytes, url: str, title: str = "") -> Page:
    if parser not in PARSERS:
        raise DocumentationParseError(f"Неизвестный парсер документации: {parser}")
    return PARSERS[parser](html, url, title)
