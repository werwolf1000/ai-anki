from server.practice_projects import project, text

PROJECTS = [
    project("python-tasks", "Менеджер задач", "python", [1, 2, 3],
            "Соберите консольную программу: задачи, проверка ввода, JSON-хранилище и восстановление списка.",
            "python", {
                "tasks.py": text('''
                    import json
                    from pathlib import Path

                    def add_task(tasks, title):
                        # TODO(human): непустое название, новый id, исходный список не изменять.
                        raise NotImplementedError("Добавление задачи")

                    def complete_task(tasks, task_id):
                        # TODO(human): пометить задачу выполненной; неизвестный id -> KeyError.
                        raise NotImplementedError("Завершение задачи")

                    def save_tasks(path, tasks):
                        # TODO(human): сохранить UTF-8 JSON.
                        raise NotImplementedError("Сохранение")

                    def load_tasks(path):
                        # TODO(human): прочитать список; если файла нет, вернуть [].
                        raise NotImplementedError("Загрузка")
                '''),
                "main.py": text('''
                    from pathlib import Path
                    from tasks import add_task, complete_task, save_tasks, load_tasks

                    if __name__ == "__main__":
                        Path("artifacts").mkdir(exist_ok=True)
                        tasks = add_task([], "Написать первый проект")
                        tasks = complete_task(tasks, tasks[0]["id"])
                        save_tasks("artifacts/tasks.json", tasks)
                        print(load_tasks("artifacts/tasks.json"))
                '''),
                "README.md": "# Менеджер задач\n\nЗапуск: python main.py\nНачните с tasks.py. Формат: {id: int, title: str, done: bool}.\n",
            }, [
                ("Создать задачу", "Реализуйте add_task. Обрежьте пробелы, отклоните пустое название через ValueError. id — max существующих id + 1. Верните новый список; done=False."),
                ("Завершить задачу", "Реализуйте complete_task без изменения исходного списка и его словарей. При неизвестном id поднимайте KeyError."),
                ("Сохранить результат", "Реализуйте save_tasks и load_tasks. Сохраняйте русские буквы в UTF-8. Несуществующий файл означает пустой список."),
            ], '''
                import sys, tempfile
                from pathlib import Path
                sys.path.insert(0, str(Path.cwd()))
                from tasks import add_task, complete_task, save_tasks, load_tasks
                stage = int(sys.argv[1])
                original = [{"id": 3, "title": "Old", "done": False}]
                items = add_task(original, "  Новая  ")
                assert len(original) == 1 and items[-1] == {"id": 4, "title": "Новая", "done": False}
                try: add_task([], "  ")
                except ValueError: pass
                else: raise AssertionError("Пустое название должно отклоняться")
                if stage >= 1:
                    done = complete_task(items, 4)
                    assert done[-1]["done"] and not items[-1]["done"]
                    try: complete_task(items, 999)
                    except KeyError: pass
                    else: raise AssertionError("Неизвестный id должен вызывать KeyError")
                if stage >= 2:
                    with tempfile.TemporaryDirectory() as directory:
                        path = Path(directory) / "tasks.json"
                        assert load_tasks(path) == []
                        save_tasks(path, items)
                        assert load_tasks(path) == items and "Новая" in path.read_text(encoding="utf-8")
                print("AI_ANKI_CHECK_OK:" + str(stage))
            ''', {
                "tasks.py": text('''
                    import json
                    from pathlib import Path

                    def add_task(tasks, title):
                        title = title.strip()
                        if not title:
                            raise ValueError("Нужно название")
                        return [*tasks, {"id": max((t["id"] for t in tasks), default=0) + 1, "title": title, "done": False}]

                    def complete_task(tasks, task_id):
                        if not any(t["id"] == task_id for t in tasks):
                            raise KeyError(task_id)
                        return [dict(t, done=True) if t["id"] == task_id else dict(t) for t in tasks]

                    def save_tasks(path, tasks):
                        Path(path).write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")

                    def load_tasks(path):
                        path = Path(path)
                        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
                '''),
            }),
    project("python-data", "От CSV к отчёту", "python", [10, 11, 12],
            "Очистите данные о продажах, рассчитайте выручку и постройте график. Результаты можно скачать.",
            "python-data", {
                "sales.csv": "region,amount\nNorth,120\nSouth,80\nNorth,30\nSouth,invalid\nWest,50\nWest,-10\n",
                "analysis.py": text('''
                    import pandas as pd

                    def clean_sales(frame):
                        # TODO(human): числовой amount, удаление пропусков и отрицательных сумм.
                        raise NotImplementedError("Очистка таблицы")

                    def summarize(frame):
                        # TODO(human): словарь region -> сумма, значения float.
                        raise NotImplementedError("Агрегирование")

                    def plot_report(summary, path):
                        # TODO(human): столбчатый график с подписями; сохранить и закрыть figure.
                        raise NotImplementedError("Визуализация")
                '''),
                "main.py": text('''
                    import json
                    from pathlib import Path
                    import pandas as pd
                    from analysis import clean_sales, summarize, plot_report

                    if __name__ == "__main__":
                        Path("artifacts").mkdir(exist_ok=True)
                        result = summarize(clean_sales(pd.read_csv("sales.csv")))
                        Path("artifacts/report.json").write_text(json.dumps(result, indent=2))
                        plot_report(result, "artifacts/report.png")
                        print(json.dumps(result, ensure_ascii=False, indent=2))
                '''),
            }, [
                ("Очистить таблицу", "В clean_sales преобразуйте amount через to_numeric(errors='coerce'). Удалите пропуски в region/amount и отрицательные суммы. Исходный DataFrame не меняйте."),
                ("Рассчитать выручку", "В summarize сгруппируйте строки по region и верните словарь сумм. Для приложенного CSV результат: North=150, South=80, West=50."),
                ("Построить график", "В plot_report постройте столбцы, подпишите оси и сохраните PNG по переданному пути. Закройте figure. Запустите main.py и скачайте отчёт."),
            ], '''
                import sys, tempfile
                from pathlib import Path
                sys.path.insert(0, str(Path.cwd()))
                import pandas as pd
                from analysis import clean_sales, summarize, plot_report
                stage = int(sys.argv[1])
                raw = pd.DataFrame({"region": ["A", "A", "B", "B", None], "amount": ["2", "3", "bad", "-1", "4"]})
                before = raw.copy(deep=True)
                cleaned = clean_sales(raw)
                assert len(cleaned) == 2 and float(cleaned.amount.sum()) == 5
                pd.testing.assert_frame_equal(raw, before)
                if stage >= 1:
                    assert summarize(cleaned) == {"A": 5.0}
                if stage >= 2:
                    with tempfile.TemporaryDirectory() as directory:
                        path = Path(directory) / "plot.png"
                        plot_report({"A": 5.0, "B": 7.0}, path)
                        assert path.read_bytes().startswith(b"\\x89PNG"), "Ожидается PNG"
                print("AI_ANKI_CHECK_OK:" + str(stage))
            ''', {
                "analysis.py": text('''
                    import pandas as pd
                    import matplotlib
                    matplotlib.use("Agg")
                    import matplotlib.pyplot as plt

                    def clean_sales(frame):
                        result = frame.copy()
                        result["amount"] = pd.to_numeric(result["amount"], errors="coerce")
                        result = result.dropna(subset=["region", "amount"])
                        return result.loc[result["amount"] >= 0].copy()

                    def summarize(frame):
                        return {str(k): float(v) for k, v in frame.groupby("region")["amount"].sum().items()}

                    def plot_report(summary, path):
                        fig, ax = plt.subplots()
                        ax.bar(list(summary), list(summary.values()))
                        ax.set(xlabel="Region", ylabel="Revenue")
                        fig.tight_layout()
                        fig.savefig(path)
                        plt.close(fig)
                '''),
            }),
    project("python-flask", "Веб-приложение заметок", "python", [4, 5, 7],
            "Создайте Flask-приложение с JSON API, SQLite и HTML-страницей. Проверьте его без внешней сети.",
            "python", {
                "app.py": text('''
                    import sqlite3
                    from flask import Flask, g, jsonify, request, render_template

                    def create_app(database="notes.sqlite"):
                        app = Flask(__name__)
                        conn = sqlite3.connect(database)
                        try:
                            conn.execute("CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY, title TEXT NOT NULL)")
                            conn.commit()
                        finally:
                            conn.close()

                        def get_db():
                            if "db" not in g:
                                g.db = sqlite3.connect(database)
                            return g.db

                        @app.teardown_appcontext
                        def close_db(error):
                            conn = g.pop("db", None)
                            if conn is not None:
                                conn.close()

                        @app.get("/api/notes")
                        def list_notes():
                            # TODO(human): вернуть JSON-массив словарей id/title, ORDER BY id.
                            return jsonify([])

                        @app.post("/api/notes")
                        def add_note():
                            # TODO(human): title — непустая строка до 80 символов, иначе 422.
                            # Через get_db(): параметризованный INSERT, commit, JSON id/title с кодом 201.
                            return {"error": "Реализуйте создание заметки"}, 501

                        @app.get("/")
                        def index():
                            rows = get_db().execute("SELECT id, title FROM notes ORDER BY id").fetchall()
                            return render_template("index.html", notes=[dict(id=r[0], title=r[1]) for r in rows])

                        return app
                '''),
                "templates/index.html": "<!doctype html><html lang=\"ru\"><meta charset=\"utf-8\"><title>Заметки</title><style>body{font:18px system-ui;max-width:700px;margin:40px auto;padding:20px}li{padding:8px}</style><h1>Мои заметки</h1><ul>{% for note in notes %}<li>{{ note.title }}</li>{% else %}<li>Пока нет заметок</li>{% endfor %}</ul></html>\n",
                "main.py": text('''
                    from app import create_app
                    from pathlib import Path

                    if __name__ == "__main__":
                        app = create_app()
                        with app.test_client() as client:
                            response = client.post("/api/notes", json={"title": "Мой первый Flask-проект"})
                            print("POST /api/notes", response.status_code, response.json)
                            print("GET /api/notes", client.get("/api/notes").json)
                            Path("artifacts").mkdir(exist_ok=True)
                            Path("artifacts/preview.html").write_text(client.get("/").get_data(as_text=True), encoding="utf-8")
                '''),
            }, [
                ("Создать заметку", "Реализуйте POST /api/notes: проверьте JSON и title, обрежьте пробелы; неверный ввод — 422. Используйте параметры SQL и верните id/title с кодом 201."),
                ("Прочитать и сохранить", "Реализуйте GET /api/notes. При переданном пути базы заметки должны сохраняться между созданием экземпляров приложения."),
                ("Показать страницу", "Проверьте шаблон: пользовательские заголовки должны экранироваться. Запустите main.py и откройте предпросмотр HTML-ответа."),
            ], '''
                import sys, tempfile
                from pathlib import Path
                sys.path.insert(0, str(Path.cwd()))
                from app import create_app
                stage = int(sys.argv[1])
                with tempfile.TemporaryDirectory() as directory:
                    path = str(Path(directory) / "notes.db")
                    app = create_app(path)
                    with app.test_client() as client:
                        assert client.post("/api/notes", json={"title": "  "}).status_code == 422
                        assert client.post("/api/notes", json={"title": 123}).status_code == 422
                        response = client.post("/api/notes", json={"title": "  Hello  "})
                        assert response.status_code == 201 and response.json["title"] == "Hello"
                        if stage >= 1:
                            assert client.get("/api/notes").json == [{"id": response.json["id"], "title": "Hello"}]
                        if stage >= 2:
                            client.post("/api/notes", json={"title": "<script>alert(1)</script>"})
                            html = client.get("/").get_data(as_text=True)
                            assert "Hello" in html and "&lt;script&gt;" in html and "<script>" not in html
                    if stage >= 1:
                        with create_app(path).test_client() as client:
                            assert client.get("/api/notes").json[0]["title"] == "Hello"
                print("AI_ANKI_CHECK_OK:" + str(stage))
            ''', {
                "app.py": text('''
                    import sqlite3
                    from flask import Flask, g, jsonify, request, render_template

                    def create_app(database="notes.sqlite"):
                        app = Flask(__name__)
                        conn = sqlite3.connect(database)
                        try:
                            conn.execute("CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY, title TEXT NOT NULL)")
                            conn.commit()
                        finally:
                            conn.close()

                        def get_db():
                            if "db" not in g:
                                g.db = sqlite3.connect(database)
                            return g.db

                        @app.teardown_appcontext
                        def close_db(error):
                            conn = g.pop("db", None)
                            if conn is not None:
                                conn.close()

                        @app.get("/api/notes")
                        def list_notes():
                            return jsonify([dict(id=r[0], title=r[1]) for r in get_db().execute("SELECT id, title FROM notes ORDER BY id")])

                        @app.post("/api/notes")
                        def add_note():
                            data = request.get_json(silent=True)
                            title = data.get("title") if isinstance(data, dict) else None
                            if not isinstance(title, str) or not 1 <= len(title.strip()) <= 80:
                                return {"error": "Нужно название до 80 символов"}, 422
                            title = title.strip()
                            conn = get_db()
                            cursor = conn.execute("INSERT INTO notes(title) VALUES (?)", (title,))
                            conn.commit()
                            return {"id": cursor.lastrowid, "title": title}, 201

                        @app.get("/")
                        def index():
                            rows = get_db().execute("SELECT id, title FROM notes ORDER BY id").fetchall()
                            return render_template("index.html", notes=[dict(id=r[0], title=r[1]) for r in rows])

                        return app
                '''),
            }, preview=True),
]

# The input pipeline is provided; learners implement the network and training.
ML_MAIN = text('''
    import json
    from pathlib import Path
    import numpy as np
    import torch
    from sklearn.datasets import load_iris
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler
    from network import make_model, train_model, predict

    def data():
        x, y = load_iris(return_X_y=True)
        xr, xt, yr, yt = train_test_split(x, y, test_size=0.2, stratify=y, random_state=42)
        scaler = StandardScaler().fit(xr)
        return (torch.tensor(scaler.transform(xr), dtype=torch.float32), torch.tensor(yr, dtype=torch.long),
                torch.tensor(scaler.transform(xt), dtype=torch.float32), torch.tensor(yt, dtype=torch.long), scaler)

    if __name__ == "__main__":
        torch.manual_seed(42)
        torch.set_num_threads(1)
        xr, yr, xt, yt, scaler = data()
        model = make_model()
        history = train_model(model, xr, yr, epochs=120)
        accuracy = (predict(model, xt) == yt).float().mean().item()
        Path("artifacts").mkdir(exist_ok=True)
        torch.save({"state_dict": model.state_dict(), "mean": scaler.mean_.tolist(), "scale": scaler.scale_.tolist()}, "artifacts/model.pt")
        metrics = {"accuracy": accuracy, "initial_loss": history[0], "final_loss": history[-1]}
        Path("artifacts/metrics.json").write_text(json.dumps(metrics, indent=2))
        print(json.dumps(metrics, indent=2))
''')
PROJECTS.append(project("python-neural", "Первая нейросеть на PyTorch", "python", [13, 14, 15, 17],
    "Обучите сеть 4 → 16 → 3 на Iris, проверьте предсказания и скачайте веса. Выполнение на CPU.",
    "python-ml", {"main.py": ML_MAIN, "network.py": text('''
        import torch
        from torch import nn

        def make_model():
            # TODO(human): Linear(4,16), ReLU, Linear(16,3), без Softmax.
            raise NotImplementedError("Архитектура сети")

        def train_model(model, x, y, epochs=120):
            # TODO(human): Adam(lr=0.02), CrossEntropyLoss, полный цикл; список loss.
            raise NotImplementedError("Обучение")

        def predict(model, x):
            # TODO(human): eval, inference_mode, argmax(dim=1).
            raise NotImplementedError("Предсказание")
    ''')}, [
        ("Построить сеть", "Реализуйте make_model: четыре входа, скрытый слой 16, ReLU, три logits. Объясните наставнику, почему Softmax пока не нужен."),
        ("Обучить параметры", "В train_model создайте Adam с lr=0.02 и CrossEntropyLoss. На каждой эпохе: train, zero_grad, forward, backward, step. Верните список числовых loss."),
        ("Получить предсказание", "Реализуйте predict с eval и inference_mode. Верните индексы классов. Запустите программу, скачайте веса и метрики. Test используется только для итоговой оценки; подбор параметров требует отдельной validation-выборки."),
    ], '''
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path.cwd()))
        import torch
        from network import make_model, train_model, predict
        from main import data
        stage = int(sys.argv[1])
        torch.manual_seed(42)
        torch.set_num_threads(1)
        model = make_model()
        assert tuple(model(torch.zeros(2,4)).shape) == (2,3)
        assert not any(isinstance(m, torch.nn.Softmax) for m in model.modules())
        if stage >= 1:
            xr, yr, xt, yt, _ = data()
            history = train_model(model, xr, yr, epochs=120)
            assert len(history) == 120 and history[-1] < history[0] * 0.6
            if stage >= 2:
                result = predict(model, xt)
                assert tuple(result.shape) == tuple(yt.shape) and not result.requires_grad
                assert (result == yt).float().mean().item() >= 0.75
        print("AI_ANKI_CHECK_OK:" + str(stage))
    ''', {"network.py": text('''
        import torch
        from torch import nn

        def make_model():
            return nn.Sequential(nn.Linear(4,16), nn.ReLU(), nn.Linear(16,3))

        def train_model(model, x, y, epochs=120):
            optimizer = torch.optim.Adam(model.parameters(), lr=0.02)
            loss_fn = nn.CrossEntropyLoss()
            history = []
            for _ in range(epochs):
                model.train()
                optimizer.zero_grad()
                loss = loss_fn(model(x), y)
                loss.backward()
                optimizer.step()
                history.append(loss.item())
            return history

        def predict(model, x):
            model.eval()
            with torch.inference_mode():
                return model(x).argmax(dim=1)
    ''')}))
