#!/usr/bin/env python3
"""Generate tkinter.ttk deck (themed widgets)."""
from __future__ import annotations

import json
from pathlib import Path


def theory(q: str, ref: str) -> dict:
    return {"question": q, "reference": ref}


def code(q: str, task: str, snippet: str, ref: str) -> dict:
    return {
        "card_type": "code",
        "question": q,
        "task": task,
        "code": snippet.strip(),
        "reference": ref.strip(),
    }


def build_cards() -> list[dict]:
    cards: list[dict] = []

    intro = [
        theory("Что такое ttk в Python?", "Подмодуль tkinter.ttk — themed widgets. Использует нативные стили ОС (Windows/macOS/Linux), в отличие от классических tk-виджетов."),
        theory("Чем ttk.Button отличается от tk.Button?", "ttk.Button рисуется темой ttk; tk.Button — классический вид. API похож, но стилизация через ttk.Style."),
        theory("Как импортировать ttk?", "import tkinter as tk\\nfrom tkinter import ttk — или from tkinter.ttk import Button, ..."),
        theory("Нужен ли root для ttk?", "Да, как и для tkinter: root = tk.Tk(); затем ttk.Frame(root) и другие виджеты."),
        theory("pack vs grid vs place с ttk?", "Те же менеджеры геометрии tkinter: .pack(), .grid(), .place() работают для ttk-виджетов."),
        theory("Что такое ttk.Style?", "Объект для настройки тем и стилей: Style().theme_use('clam'), style.configure('TButton', ...)."),
        theory("Как узнать доступные темы?", "style = ttk.Style(); style.theme_names() — например 'clam', 'alt', 'default', 'classic' на Linux."),
        theory("theme_use()?", "style.theme_use('clam') — переключить тему для всех ttk-виджетов в приложении."),
        theory("Что такое layout в ttk.Style?", "style.layout('TButton') — описание элементов отрисовки виджета (element tree темы)."),
        theory("configure vs map в Style?", "configure — статические опции; map — динамические по state (active, disabled)."),
        theory("state у ttk-виджетов?", "state=['disabled'] или state='readonly' (Combobox/Entry). state(['!disabled']) для включения."),
        theory("ttk widget .configure?", "Виджет.configure(text='OK') или cget('text') — как у tk, плюс style, state."),
        theory("Класс vs ttk виджет Treeview?", "Treeview только в ttk — таблицы и деревья с колонками."),
        theory("Notebook в ttk?", "Вкладки: nb = ttk.Notebook(parent); nb.add(frame, text='Tab 1')."),
        theory("Progressbar modes?", "mode='determinate' (value/maximum) или 'indeterminate' (start/stop анимация)."),
        theory("Combobox readonly?", "state='readonly' — выбор из values без произвольного ввода."),
        theory("Separator orient?", "orient='horizontal' или 'vertical' — линия-разделитель."),
        theory("Panedwindow?", "Разделитель панелей: pw.add(child1); pw.add(child2); orient horizontal/vertical."),
        theory("Sizegrip?", "Уголок для resize окна — обычно в правом нижнем углу status bar."),
        theory("ttk.Spinbox?", "Числовой ввод со стрелками (Python 3.7+ в ttk, раньше только tk.Spinbox)."),
        theory("Scrollbar связь?", "scrollbar = ttk.Scrollbar(..., command=widget.yview); widget.configure(yscrollcommand=scrollbar.set)."),
        theory("Treeview show parameter?", "show='tree' — только дерево; show='headings' — таблица; 'tree headings' — оба."),
        theory("Treeview columns?", "columns=('name','age'); heading('#0'); column('#0'); insert('', END, values=(...))."),
        theory("Treeview selection?", "selection() — iids; bind('<<TreeviewSelect>>', handler)."),
        theory("Treeview tags?", "tags=('odd',) + tag_configure для цветов строк."),
        theory("virtual events ttk?", "<<TreeviewSelect>>, <<NotebookTabChanged>>, <<ComboboxSelected>> — bind на них."),
        theory("ttk.Frame vs tk.Frame?", "ttk.Frame участвует в теме; tk.Frame — простой контейнер без themed border."),
        theory("LabelFrame?", "ttk.LabelFrame(parent, text='Group') — группа с рамкой и заголовком."),
        theory("padding в ttk?", "padding=10 в pack/grid или style; LabelFrame padding для внутренних отступов."),
        theory("weight в grid?", "parent.columnconfigure(0, weight=1) — растягивание при resize для ttk grid layouts."),
        theory("ttk и DPI scaling?", "На HiDPI иногда нужен tk scaling или platform-specific tweaks; ttk следует теме ОС."),
        theory("Когда оставить tk виджет?", "Text, Canvas, Menu — только в classic tk; ttk не заменяет всё."),
        theory("ttk.Entry validate?", "validate='key' + validatecommand — как tk.Entry; для сложного ввода часто trace variable."),
        theory("StringVar и ttk?", "textvariable=tk.StringVar() — работает с ttk.Entry, Label, Button, Combobox."),
        theory("IntVar DoubleVar?", "Для Scale, Spinbox, Progressbar valuevariable=IntVar()."),
        theory("after() с ttk?", "root.after(ms, callback) — таймеры UI; не блокировать mainloop долгими операциями."),
        theory("mainloop?", "root.mainloop() — event loop; все ttk обновления в главном потоке."),
        theory("destroy widget?", "widget.destroy() — удалить; master.quit() vs master.destroy() для выхода."),
        theory("withdraw/deiconify?", "root.withdraw() скрыть окно; deiconify() показать — splash/loader pattern."),
        theory("transient и grab?", "toplevel.transient(parent) — дочернее окно; grab_set() модальный диалог."),
        theory("ttk в PyQt проектах?", "Не смешивают — ttk только в tkinter apps. У пользователя может быть tkinter client отдельно."),
    ]
    cards.extend(intro)

    widgets = [
        "Button", "Label", "Entry", "Frame", "LabelFrame", "Menubutton", "Panedwindow",
        "Notebook", "Progressbar", "Radiobutton", "Scale", "Scrollbar", "Separator",
        "Sizegrip", "Spinbox", "Treeview", "Combobox", "Checkbutton",
    ]
    for w in widgets:
        cards.append(theory(f"ttk.{w} — назначение?", f"Виджет ttk.{w} — themed элемент UI. Создание: ttk.{w}(parent, **options)."))
        cards.append(theory(f"Типичные опции ttk.{w}?", f"Общие: style, takefocus, cursor, state. Специфичные — см. docs для ttk.{w}."))

    style_topics = [
        ("TButton", "Стиль кнопок: padding, font, width"),
        ("TLabel", "Стиль меток: foreground, background, anchor"),
        ("TEntry", "Поля ввода: fieldbackground, bordercolor"),
        ("TFrame", "Контейнер: relief, borderwidth через theme"),
        ("Treeview", "Heading и Cell стили: Treeview.Heading, Treeview"),
        ("TNotebook", "Tab позиция: tabposition n/s/e/w"),
        ("TProgressbar", "thickness, troughcolor"),
        ("TCombobox", "arrowsize, padding"),
        ("TRadiobutton", "indicatorcolor, indicatormargin"),
        ("TCheckbutton", "indicator element в layout"),
    ]
    for name, desc in style_topics:
        cards.append(theory(f"Стиль {name} в ttk.Style?", f"style.configure('{name}', ...); style.map('{name}', ...). {desc}"))

    code_cards = [
        code(
            "Notebook: вкладки не добавлены.",
            "Добавь два Frame как вкладки «Главная» и «Настройки».",
            """import tkinter as tk
from tkinter import ttk

root = tk.Tk()
nb = ttk.Notebook(root)
nb.pack(fill='both', expand=True)
root.mainloop()""",
            """tab1 = ttk.Frame(nb)
tab2 = ttk.Frame(nb)
nb.add(tab1, text='Главная')
nb.add(tab2, text='Настройки')""",
        ),
        code(
            "Treeview без headings.",
            "Настрой колонки id и name, заголовки, одну строку.",
            """tree = ttk.Treeview(parent)
tree.pack()""",
            """tree = ttk.Treeview(parent, columns=('id', 'name'), show='headings')
tree.heading('id', text='ID')
tree.heading('name', text='Name')
tree.column('id', width=60)
tree.insert('', 'end', values=(1, 'Alice'))""",
        ),
        code(
            "Scrollbar не связан с Listbox.",
            "Свяжи Listbox и ttk.Scrollbar.",
            """lb = tk.Listbox(frame)
sb = ttk.Scrollbar(frame, orient='vertical')
lb.pack(side='left')
sb.pack(side='right')""",
            """lb = tk.Listbox(frame)
sb = ttk.Scrollbar(frame, orient='vertical', command=lb.yview)
lb.configure(yscrollcommand=sb.set)
lb.pack(side='left', fill='both', expand=True)
sb.pack(side='right', fill='y')""",
        ),
        code(
            "Progressbar determinate.",
            "Установи maximum=100 и value=40.",
            """pb = ttk.Progressbar(root, length=200)
pb.pack()""",
            """pb = ttk.Progressbar(root, length=200, mode='determinate', maximum=100, value=40)
pb.pack()""",
        ),
        code(
            "Combobox без values.",
            "Задай values и readonly state.",
            """cb = ttk.Combobox(root)
cb.pack()""",
            """cb = ttk.Combobox(root, values=['ru', 'en', 'de'], state='readonly')
cb.pack()
cb.current(0)""",
        ),
        code(
            "Кнопка не растягивается в grid.",
            "Сделай column weight=1 и sticky='ew'.",
            """btn = ttk.Button(root, text='Save')
btn.grid(row=0, column=0)""",
            """root.columnconfigure(0, weight=1)
btn = ttk.Button(root, text='Save')
btn.grid(row=0, column=0, sticky='ew', padx=5, pady=5)""",
        ),
        code(
            "Style не применён.",
            "Создай стиль Accent.TButton и примени к кнопке.",
            """btn = ttk.Button(root, text='Go')
btn.pack()""",
            """style = ttk.Style()
style.configure('Accent.TButton', font=('Segoe UI', 10, 'bold'))
btn = ttk.Button(root, text='Go', style='Accent.TButton')
btn.pack()""",
        ),
        code(
            "Disabled state.",
            "Отключи Entry при старте.",
            """entry = ttk.Entry(root)
entry.pack()""",
            """entry = ttk.Entry(root, state='disabled')
entry.pack()
# entry.state(['!disabled']) — включить""",
        ),
        code(
            "Panedwindow одна панель.",
            "Добавь два Frame в horizontal Panedwindow.",
            """pw = ttk.Panedwindow(root, orient='horizontal')
pw.pack(fill='both', expand=True)""",
            """left = ttk.Frame(pw, width=200)
right = ttk.Frame(pw)
pw.add(left, weight=1)
pw.add(right, weight=3)""",
        ),
        code(
            "Bind TreeviewSelect.",
            "Выведи selection в handler.",
            """def on_select(event):
    pass

tree.bind('<Button-1>', on_select)""",
            """def on_select(event):
    sel = tree.selection()
    if sel:
        print(tree.item(sel[0], 'values'))

tree.bind('<<TreeviewSelect>>', on_select)""",
        ),
        code(
            "Radiobutton group.",
            "Свяжи два Radiobutton одной IntVar.",
            """ttk.Radiobutton(root, text='A').pack()
ttk.Radiobutton(root, text='B').pack()""",
            """choice = tk.IntVar(value=1)
ttk.Radiobutton(root, text='A', variable=choice, value=1).pack()
ttk.Radiobutton(root, text='B', variable=choice, value=2).pack()""",
        ),
        code(
            "Checkbutton variable.",
            "Используй BooleanVar для чекбокса.",
            """var = tk.StringVar()
ttk.Checkbutton(root, text='OK', variable=var).pack()""",
            """var = tk.BooleanVar(value=False)
ttk.Checkbutton(root, text='OK', variable=var).pack()""",
        ),
        code(
            "LabelFrame форма.",
            "Помести Entry в LabelFrame с заголовком «Логин».",
            """entry = ttk.Entry(root)
entry.pack()""",
            """lf = ttk.LabelFrame(root, text='Логин', padding=10)
lf.pack(fill='x', padx=10, pady=5)
ttk.Entry(lf).pack(fill='x')""",
        ),
        code(
            "Scale без variable.",
            "Привяжи Scale к DoubleVar и Label.",
            """scale = ttk.Scale(root, from_=0, to=100)
scale.pack()""",
            """vol = tk.DoubleVar(value=50)
scale = ttk.Scale(root, from_=0, to=100, variable=vol)
lbl = ttk.Label(root, textvariable=vol)
scale.pack(); lbl.pack()""",
        ),
        code(
            "Spinbox range.",
            "from_=0, to=10, increment=1.",
            """sp = ttk.Spinbox(root)
sp.pack()""",
            """sp = ttk.Spinbox(root, from_=0, to=10, increment=1)
sp.pack()""",
        ),
        code(
            "Separator в toolbar.",
            "Vertical separator между кнопками.",
            """# между btn1 и btn2 в horizontal frame""",
            """ttk.Separator(toolbar, orient='vertical').pack(side='left', fill='y', padx=4)""",
        ),
        code(
            "Theme switch.",
            "Переключи тему на 'clam'.",
            """root = tk.Tk()""",
            """root = tk.Tk()
style = ttk.Style()
style.theme_use('clam')""",
        ),
        code(
            "map hover button.",
            "Тёмнее background при active.",
            """style.configure('TButton', padding=6)""",
            """style.configure('TButton', padding=6)
style.map('TButton', background=[('active', '#dce4f2')])""",
        ),
        code(
            "Treeview delete all.",
            "Очисти все строки перед reload.",
            """for item in tree.get_children():
    pass""",
            """for item in tree.get_children():
    tree.delete(item)""",
        ),
        code(
            "Combobox get value.",
            "Прочитай выбранное значение по кнопке.",
            """def save():
    pass""",
            """def save():
    lang = cb.get()
    print(lang)""",
        ),
    ]
    cards.extend(code_cards)

    patterns = [
        "форма login", "таблица данных", "master-detail", "settings dialog", "wizard steps",
        "status bar", "toolbar actions", "filterable list", "sortable tree", "themed dark",
        "responsive grid", "scrollable frame", "modal confirm", "file picker companion",
        "progress long task", "thread safe UI update", "after idle refresh", "validation entry",
        "tooltip pattern", "menu bar ttk",
    ]
    for p in patterns:
        for i in range(4):
            cards.append(theory(
                f"ttk паттерн [{p}] #{i+1}",
                f"Типичная реализация «{p}» в tkinter.ttk: Frame/Notebook/Treeview + grid weights + Style. Долгие задачи — threading + root.after для UI.",
            ))

    events = [
        "<<TreeviewSelect>>", "<<TreeviewOpen>>", "<<TreeviewClose>>",
        "<<NotebookTabChanged>>", "<<ComboboxSelected>>", "<Configure>", "<FocusIn>", "<FocusOut>",
        "<Return>", "<Escape>", "<Button-1>", "<Double-1>", "<Motion>",
    ]
    for ev in events:
        cards.append(theory(f"Событие {ev} в ttk/tk?", f"Привязка: widget.bind('{ev}', handler). event.widget — источник."))

    compare_tk = [
        ("Text widget", "Только tk.Text — многострочный редактор; ttk не имеет аналога."),
        ("Canvas", "tk.Canvas для рисования; ttk не заменяет."),
        ("Menu", "tk.Menu для menubar/context; ttk.Menubutton только кнопка с menu."),
        ("messagebox", "tkinter.messagebox — диалоги OK/Cancel."),
        ("filedialog", "filedialog.askopenfilename — выбор файлов."),
        ("colorchooser", "colorchooser.askcolor — выбор цвета."),
    ]
    for topic, ref in compare_tk:
        cards.append(theory(f"ttk + tk: {topic}?", ref))

    for w in widgets:
        for opt in ["style", "state", "takefocus", "cursor", "class"]:
            cards.append(theory(
                f"Опция {opt} у ttk.{w}?",
                f"Общая опция ttk {opt} — см. документацию ttk.{w}; настраивает поведение/вид themed widget.",
            ))

    code_templates = [
        ("grid sticky", "sticky nsew", "widget.grid(row=0)", "widget.grid(row=0, sticky='nsew')"),
        ("pack expand", "fill expand", "widget.pack()", "widget.pack(fill='both', expand=True)"),
        ("column weight", "weight config", "frame.grid()", "frame.columnconfigure(0, weight=1)"),
        ("notebook select", "select tab", "nb.add(f)", "nb.select(f)"),
        ("tree iid", "insert iid", "tree.insert('',0)", "tree.insert('', 'end', iid='row1', values=(1,'a'))"),
        ("style instance", "custom style name", "TButton", "Custom.TButton + style.configure"),
        ("state tuple", "disable btn", "state='disabled'", "btn.state(['disabled'])"),
        ("enable state", "enable", "state='normal'", "btn.state(['!disabled'])"),
        ("progress step", "step value", "pb['value']=0", "pb.step(5) or pb.configure(value=n)"),
        ("indeterminate pb", "start anim", "mode default", "pb.configure(mode='indeterminate'); pb.start(10)"),
    ]
    for i, (name, task, broken, fixed) in enumerate(code_templates):
        for n in range(3):
            cards.append(code(f"ttk [{name}] #{i}-{n}", task, broken, fixed))

    for w in widgets:
        for scenario in [
            "создание", "pack grid", "style", "state disabled", "event bind",
            "resize layout", "scroll связка", "validation", "focus order",
        ]:
            cards.append(theory(
                f"ttk.{w}: сценарий «{scenario}»?",
                f"Практика ttk.{w} — {scenario}: см. docs, используй Style/geometry managers/virtual events.",
            ))

    seen: set[str] = set()
    out: list[dict] = []
    for c in cards:
        k = c.get("question", "") + c.get("code", "")
        if k not in seen:
            seen.add(k)
            out.append(c)
    return out


def main() -> None:
    cards = build_cards()
    deck = {"name": "tkinter.ttk", "cards": cards}
    out = Path(__file__).with_name("ttk-widgets.json")
    out.write_text(json.dumps(deck, ensure_ascii=False, indent=2), encoding="utf-8")
    code_n = sum(1 for c in cards if c.get("card_type") == "code")
    print(f"Written {len(cards)} cards ({code_n} code) -> {out}")


if __name__ == "__main__":
    main()
