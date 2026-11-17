"""Контракты HTML-шаблонов документации и путь от загрузки до RAG-поиска."""
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from server.kb_parsers import DocumentationParseError, parse_document
from server.kb_sources import SOURCES, WebDoc, fetch_web_doc, load_pages, parse_sphinx_page, python_selected
from server.knowledge import KnowledgeIndexer, KnowledgeStore, chunk_page


WRAPPERS = {
    "django": ('<article id="docs-content">', '</article>'),
    "flask": ('<div class="body" role="main">', '</div>'),
    "fastapi": ('<article class="md-content__inner md-typeset">', '</article>'),
    "numpy": ('<article class="bd-article">', '</article>'),
    "pandas": ('<article class="bd-article">', '</article>'),
    "matplotlib": ('<article class="bd-article">', '</article>'),
    "sklearn": ('<article class="bd-article">', '</article>'),
    "pytorch": ('<div id="pytorch-article"><article class="bd-article">', '</article></div>'),
    "sqlalchemy": ('<div id="docs-body" role="main">', '</div>'),
}
INTRO = '<h1>Training example<a class="headerlink" href="#training">¶</a></h1><p>' + (
    'This tutorial explains how to train a classifier, validate the input and save its parameters. '
    'Training data and validation data have different roles; preprocessing must use training statistics. '
) + '</p>'
CODE = '<div class="highlight-python"><div class="highlight"><pre><span class="linenos">1</span>def train():\n    value = 1\n\n    return value\n</pre></div></div>'


def document(parser, extra="", intro=INTRO):
    start, end = WRAPPERS[parser]
    return ('<html><head><title>Site navigation</title></head><body>'
            '<nav>OUTSIDE_NAVIGATION</nav><h1>SITE_TITLE</h1>' + start + intro + extra +
            '<aside>SIDEBAR_GARBAGE</aside><div class="toctree-wrapper">TOC_GARBAGE</div>' +
            '<script>TRACKING_CODE</script>' + end + '<footer>FOOTER_GARBAGE</footer></body></html>')


class DocumentationParsersTest(unittest.TestCase):
    def test_each_site_preserves_article_code_and_citation_without_chrome(self):
        for parser in WRAPPERS:
            with self.subTest(parser=parser):
                url = 'https://docs.example.test/tutorial/first/'
                page = parse_document(parser, document(parser, CODE), url)
                self.assertEqual(page.url, url)
                self.assertEqual(page.name, url)
                self.assertTrue(page.title.endswith(': Training example'))
                self.assertIn('```python\ndef train():\n    value = 1\n\n    return value\n```', page.markdown)
                self.assertNotIn('¶', page.markdown)
                for garbage in ('OUTSIDE_NAVIGATION', 'SITE_TITLE', 'SIDEBAR_GARBAGE', 'TOC_GARBAGE', 'TRACKING_CODE', 'FOOTER_GARBAGE'):
                    self.assertNotIn(garbage, page.markdown)
                chunks = chunk_page(page)
                self.assertTrue(chunks)
                self.assertTrue(all(c.url == url for c in chunks))
                self.assertTrue(any('return value' in c.text for c in chunks))

    def test_layout_changes_are_errors_instead_of_body_fallback(self):
        for parser in WRAPPERS:
            with self.subTest(parser=parser):
                with self.assertRaises(DocumentationParseError):
                    parse_document(parser, '<body>' + INTRO + '</body>', 'https://docs.example.test/')
                with self.assertRaises(DocumentationParseError):
                    parse_document(parser, document(parser, intro='<p>No heading</p>'), 'https://docs.example.test/')
                with self.assertRaises(DocumentationParseError):
                    parse_document(parser, document(parser, intro='<h1>Unavailable</h1>'), 'https://docs.example.test/')
        with self.assertRaisesRegex(DocumentationParseError, 'Неизвестный парсер'):
            parse_document('typo', INTRO, 'https://docs.example.test/')

    def test_django_keeps_filenames_shell_and_template_languages(self):
        extra = ('<div class="code-block-caption">polls/views.py</div>' + CODE +
                 '<div class="highlight-console"><pre>$ python manage.py migrate</pre></div>'
                 '<div class="highlight-html+django"><pre>&lt;p&gt;{{ name }}&lt;/p&gt;</pre></div>'
                 '<div class="admonition warning"><p>Check permissions before saving.</p></div>')
        md = parse_document('django', document('django', extra), 'https://docs.example.test/').markdown
        self.assertIn('polls/views.py', md)
        self.assertIn('```console\n$ python manage.py migrate', md)
        self.assertIn('```html+django\n<p>{{ name }}</p>', md)
        self.assertIn('Check permissions before saving.', md)

    def test_fastapi_keeps_version_tabs_and_removes_repeated_promotion(self):
        extra = '''<details><summary>AI coding agents</summary><p>PROMO_GARBAGE</p></details>
        <div class="tabbed-set"><input type="radio"><div class="tabbed-labels">
        <label>Python 3.10+</label><label>Python 3.9+</label></div><div class="tabbed-content">
        <div class="tabbed-block"><pre><code class="language-python">value: str | None</code></pre></div>
        <div class="tabbed-block" hidden><pre><code class="language-python">value: Optional[str]</code></pre></div>
        </div></div><details><summary>Technical details</summary><p>USEFUL_EXPLANATION</p></details>'''
        md = parse_document('fastapi', document('fastapi', extra), 'https://docs.example.test/').markdown
        self.assertNotIn('PROMO_GARBAGE', md)
        self.assertIn('USEFUL_EXPLANATION', md)
        self.assertIn('#### Python 3.10+\n\n```python\nvalue: str | None', md)
        self.assertIn('#### Python 3.9+\n\n```python\nvalue: Optional[str]', md)

    def test_pandas_keeps_dataframe_headers_rows_and_notebook_prompts(self):
        extra = '''<div class="highlight-ipython"><pre>In [1]: frame.head()</pre></div>
        <table class="dataframe"><thead><tr><th></th><th>age</th><th>label</th></tr></thead>
        <tbody><tr><th>0</th><td>42</td><td>a|b</td></tr><tr><th>1</th><td>18</td><td>c</td></tr></tbody></table>'''
        md = parse_document('pandas', document('pandas', extra), 'https://docs.example.test/').markdown
        self.assertIn('```pycon\nIn [1]: frame.head()', md)
        self.assertIn('|  | age | label |\n| --- | --- | --- |\n| 0 | 42 | a\\|b |\n| 1 | 18 | c |', md)

    def test_gallery_keeps_outputs_and_drops_download_widgets(self):
        extra = (CODE + '<div class="sphx-glr-script-out highlight-none"><pre>accuracy = 0.9</pre></div>'
                 '<div class="sphx-glr-footer">DOWNLOAD_GARBAGE</div><p class="sphx-glr-timing">TIMING_GARBAGE</p>')
        for parser in ('matplotlib', 'sklearn', 'pytorch'):
            with self.subTest(parser=parser):
                md = parse_document(parser, document(parser, extra), 'https://docs.example.test/').markdown
                self.assertIn('```text\naccuracy = 0.9', md)
                self.assertIn('def train()', md)
                self.assertNotIn('DOWNLOAD_GARBAGE', md)
                self.assertNotIn('TIMING_GARBAGE', md)

    def test_sklearn_keeps_one_estimator_representation(self):
        extra = '''<div class="sk-top-container"><pre class="sk-text-repr-fallback">Pipeline(steps=[])</pre>
        <div class="sk-container">DIAGRAM_DUPLICATE</div></div>'''
        md = parse_document('sklearn', document('sklearn', extra), 'https://docs.example.test/').markdown
        self.assertEqual(md.count('Pipeline(steps=[])'), 1)
        self.assertNotIn('DIAGRAM_DUPLICATE', md)

    def test_relative_links_api_signatures_and_heading_backrefs(self):
        extra = '''<h2><a class="toc-backref" href="#toc">Session</a></h2>
        <dl><dt><code>Session.execute(statement)</code></dt><dd>Execute a statement.</dd></dl>
        <p><a href="../engine.html#connect">Connections</a> and <a href="javascript:bad()">bad</a>.</p>'''
        md = parse_document('sqlalchemy', document('sqlalchemy', extra), 'https://docs.example.test/tutorial/orm.html').markdown
        self.assertIn('## Session', md)
        self.assertIn('`Session.execute(statement)`', md)
        self.assertIn('[Connections](https://docs.example.test/engine.html#connect)', md)
        self.assertNotIn('javascript:', md)

    def test_all_python_web_sources_select_dedicated_parsers(self):
        names = ('django_docs', 'flask_docs', 'fastapi_docs', 'python_data_docs', 'sklearn_basics', 'pytorch_basics', 'sqlalchemy_docs')
        for name in names:
            source = SOURCES[name]
            for doc in source.docs:
                with self.subTest(source=name, url=doc.url):
                    self.assertIn(doc.parser, WRAPPERS)
                    response = SimpleNamespace(content=document(doc.parser, CODE).encode(), headers={'content-type': 'text/html'})
                    with patch('server.kb_sources._get', return_value=response):
                        page = fetch_web_doc(doc)
                    self.assertIn('def train()', page.markdown)
                    self.assertEqual(page.url, doc.page_url or doc.url)
        for module in ('tkinter', 'tkinter.ttk'):
            self.assertTrue(python_selected(f'library/{module}.html'))
            page = parse_sphinx_page(module, document('flask', CODE), 'https://docs.python.org/3/library/' + module + '.html')
            self.assertIn('def train()', page.markdown)

    def test_generic_web_documents_still_work(self):
        doc = WebDoc('https://docs.example.test/paper', 'Existing source')
        response = SimpleNamespace(content=('<main>' + INTRO + '</main>').encode(), headers={'content-type': 'text/html'})
        with patch('server.kb_sources._get', return_value=response):
            page = fetch_web_doc(doc)
        self.assertEqual(page.title, 'Existing source')
        self.assertIn('Training example', page.markdown)

    def test_loaded_pages_are_searchable_with_source_filter_and_citations(self):
        source = replace(SOURCES['django_docs'], docs=SOURCES['django_docs'].docs[:1])
        response = SimpleNamespace(content=document('django', CODE).encode(), headers={'content-type': 'text/html'})
        with patch('server.kb_sources._get', return_value=response):
            pages = load_pages(source, lambda _: None, lambda *_: None)
        with TemporaryDirectory() as directory:
            store = KnowledgeStore(Path(directory) / 'knowledge.db')
            try:
                store.replace_source(source.id, len(pages), [chunk for page in pages for chunk in chunk_page(page)])
                hits = store.get_chunks(store.fts_search('classifier', [source.id]))
                self.assertTrue(hits)
                self.assertTrue(all(hit['source'] == source.id and hit['url'] == source.docs[0].url for hit in hits))
                self.assertEqual(store.fts_search('classifier', ['flask_docs']), [])
                # При изменении HTML не стираем ранее рабочий индекс источника.
                before = store.stats()[source.id]['chunks']
                response.content = b'<body>Service unavailable</body>'
                with patch('server.kb_sources._get', return_value=response):
                    indexer = KnowledgeIndexer(store)
                    rag = Mock()
                    indexer._run([source.id], rag, 'embedding-test', True, {})
                self.assertIn(source.id, indexer.job.error)
                self.assertEqual(store.stats()[source.id]['chunks'], before)
                rag.embed.assert_not_called()
            finally:
                store._db.close()


if __name__ == '__main__':
    unittest.main()
