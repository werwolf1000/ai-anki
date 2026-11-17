"""Python-разработчик: от небольших приложений до первой обученной нейросети."""
from pathlib import Path
from textwrap import dedent

CHAPTERS = {}
THEORY = {}
PRACTICE = []


def lesson(chapter, title, question, answer, task, solution, extra=None):
    CHAPTERS.setdefault(chapter, []).append(title)
    THEORY[title] = [(question, answer)] + ([extra] if extra else [])
    PRACTICE.append((title, "python", task, dedent(solution).strip()))


C = "1. Основы Python"
lesson(C, "Коллекции, изменяемость и преобразование данных",
       "Чем список отличается от множества и когда нужен словарь?",
       "Список хранит последовательность с повторениями, множество — уникальные хешируемые элементы. Словарь связывает ключ со значением. Порядок вставки в dict сохраняется; порядок обхода set не используют как порядок результата.",
       "Напишите unique_names(names): уберите пробелы по краям, пустые имена и повторы, сохранив порядок первого появления.", """
       def unique_names(names):
           return list(dict.fromkeys(name.strip() for name in names if name.strip()))
       """, ("Почему изменение вложенного списка заметно через поверхностную копию?", "Поверхностная копия создаёт новый внешний контейнер, но сохраняет ссылки на вложенные объекты. Для независимой копии вложенных изменяемых данных нужен deepcopy либо явное построение новых объектов."))
lesson(C, "Условия, циклы и comprehensions",
       "Когда comprehension удобнее обычного цикла?", "Для простого преобразования и фильтрации коллекции. При сложных ветвлениях, побочных эффектах или обработке исключений читаемее обычный цикл.",
       "Напишите positive_squares(values): верните квадраты только положительных чисел; для пустого списка верните [].", """
       def positive_squares(values):
           return [value ** 2 for value in values if value > 0]
       """)
lesson(C, "Функции, аргументы и аннотации типов",
       "Почему нельзя использовать [] как изменяемый аргумент по умолчанию?", "Значение по умолчанию создаётся при определении функции и разделяется между вызовами. Обычно используют None и создают новый список внутри функции. Аннотации типов сами по себе не проверяют значения при выполнении.",
       "Напишите add_tag(tag: str, tags=None), возвращающую новый список с добавленным тегом. Исходный список не изменять.", """
       def add_tag(tag: str, tags: list[str] | None = None) -> list[str]:
           return [*(tags if tags is not None else []), tag]
       """)
lesson(C, "Исключения и проверка входных данных",
       "Почему обработчик except Exception без повторного возбуждения ошибки опасен?", "Он может скрыть дефект программы вместе с ожидаемой ошибкой ввода. Перехватывают конкретные исключения, добавляют контекст и либо исправляют ситуацию, либо передают ошибку вызывающему коду.",
       "Напишите parse_port(text): преобразуйте строку в int от 1 до 65535; при неверном вводе поднимите ValueError с понятным сообщением.", """
       def parse_port(text):
           try:
               port = int(text)
           except (TypeError, ValueError) as exc:
               raise ValueError('Порт должен быть целым числом') from exc
           if not 1 <= port <= 65535:
               raise ValueError('Порт должен быть от 1 до 65535')
           return port
       """)

C = "2. Структура приложения и ООП"
lesson(C, "Классы, dataclasses и композиция",
       "Для чего подходит dataclass?", "Для объектов с явно описанными полями: dataclass создаёт __init__, __repr__ и сравнение. Бизнес-правила и проверку значений по-прежнему пишут явно; внешние сервисы удобнее передавать через композицию.",
       "Создайте dataclass Product(name, price), отклоняющий отрицательную цену в __post_init__.", """
       from dataclasses import dataclass

       @dataclass
       class Product:
           name: str
           price: float

           def __post_init__(self):
               if self.price < 0:
                   raise ValueError('Цена не может быть отрицательной')
       """)
lesson(C, "Модули, пакеты и точка входа",
       "Зачем нужен if __name__ == '__main__'?", "Он отделяет запуск программы от импорта её функций. Импорт не должен запускать обучение модели, сервер или окно: это мешает тестированию и переиспользованию.",
       "Создайте модуль с greeting(name), main() и защитой точки входа. При импорте ничего не печатать.", """
       def greeting(name):
           return f'Привет, {name}!'

       def main():
           print(greeting('Python'))

       if __name__ == '__main__':
           main()
       """)
lesson(C, "Генераторы и потоковая обработка",
       "Чем генератор помогает при обработке большого файла?", "Он отдаёт элементы по мере запроса и не хранит весь результат в памяти. Важно не превращать его сразу в list, если требуется сохранить потоковую обработку.",
       "Напишите генератор nonempty_lines(path), открывающий UTF-8 файл и выдающий непустые строки без пробелов по краям.", """
       def nonempty_lines(path):
           with open(path, encoding='utf-8') as stream:
               for line in stream:
                   if value := line.strip():
                       yield value
       """)

C = "3. Инструменты, файлы и автоматизация"
lesson(C, "venv, pip и воспроизводимое окружение",
       "Почему зависимости проекта устанавливают в виртуальное окружение?", "Окружение изолирует пакеты проекта от других программ. Версию Python и зависимости записывают в документации и файле зависимостей; python -m pip обращается к pip выбранного интерпретатора.",
       "Напишите скрипт, печатающий путь интерпретатора и признак запуска в venv через sys.prefix и sys.base_prefix.", """
       import sys
       print(sys.executable)
       print('venv:', sys.prefix != sys.base_prefix)
       """)
lesson(C, "pathlib, JSON и CSV",
       "Почему при чтении текстовых файлов следует указывать encoding?", "Кодировка по умолчанию зависит от окружения. Явный UTF-8 делает обмен воспроизводимым; CSV лучше читать csv.DictReader, учитывающим кавычки и разделители, а не split(',').",
       "Напишите csv_to_json(source, target): прочитайте CSV с заголовком и сохраните список словарей в UTF-8 JSON с русскими буквами.", """
       import csv
       import json
       from pathlib import Path

       def csv_to_json(source, target):
           with open(source, encoding='utf-8', newline='') as stream:
               rows = list(csv.DictReader(stream))
           Path(target).write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')
       """)
lesson(C, "argparse и командная строка",
       "Зачем учебной программе обучения модели параметры командной строки?", "Параметры позволяют менять число эпох, seed и выходной каталог без редактирования кода. Их значения валидируют до запуска вычислений и сохраняют с результатом эксперимента.",
       "Создайте argparse-параметр --epochs с целым значением по умолчанию 100. При значении меньше 1 завершите разбор с ошибкой.", """
       import argparse
       parser = argparse.ArgumentParser()
       parser.add_argument('--epochs', type=int, default=100)
       args = parser.parse_args()
       if args.epochs < 1:
           parser.error('--epochs должен быть положительным')
       print(args.epochs)
       """)

C = "4. HTTP и асинхронность"
lesson(C, "requests и обработка HTTP-ошибок",
       "Какие проверки нужны при загрузке JSON через requests?", "Задают таймаут, проверяют HTTP-статус, затем разбирают JSON и проверяют его структуру. Успешное соединение не означает успешный HTTP-ответ, а ответ 200 не гарантирует нужную JSON-схему.",
       "Напишите fetch_json(url), задающую timeout=10, проверяющую статус и возвращающую разобранный JSON.", """
       import requests

       def fetch_json(url):
           response = requests.get(url, timeout=10)
           response.raise_for_status()
           return response.json()
       """)
lesson(C, "asyncio и конкурентный ввод-вывод",
       "Ускорит ли async def само по себе обучение нейросети?", "Нет. Asyncio помогает совмещать ожидающие операции ввода-вывода. Вычисления без await блокируют цикл событий; обучение выносят в рабочий процесс или отдельную задачу.",
       "Напишите async-функцию fetch_many(urls) с httpx.AsyncClient: параллельно получите JSON, проверяя статус каждого ответа.", """
       import asyncio
       import httpx

       async def fetch_many(urls):
           async with httpx.AsyncClient(timeout=10) as client:
               async def fetch(url):
                   response = await client.get(url)
                   response.raise_for_status()
                   return response.json()
               return await asyncio.gather(*(fetch(url) for url in urls))
       """)

C = "5. Базы данных"
lesson(C, "SQLite, параметры запросов и транзакции",
       "Почему нельзя подставлять пользовательскую строку в SQL через f-string?", "Ввод может изменить смысл SQL-запроса. Значения передают параметрами драйвера; имена таблиц и полей выбирают из разрешённого набора. Транзакция объединяет изменения в одну согласованную операцию.",
       "Напишите save_note(conn, title): создайте таблицу notes при необходимости и вставьте title параметризованным запросом внутри транзакции.", """
       def save_note(conn, title):
           with conn:
               conn.execute('CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY, title TEXT NOT NULL)')
               conn.execute('INSERT INTO notes (title) VALUES (?)', (title,))
       """)
lesson(C, "SQLAlchemy: модели и Session",
       "Какова роль Session в SQLAlchemy?", "Session управляет единицей работы, состоянием ORM-объектов и транзакцией. Она не является общим потокобезопасным контейнером: её жизненный цикл обычно ограничивают запросом или задачей.",
       "На SQLAlchemy 2 опишите Base и модель Note с целочисленным первичным ключом id и строковым title длиной до 200.", """
       from sqlalchemy import String
       from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

       class Base(DeclarativeBase):
           pass

       class Note(Base):
           __tablename__ = 'notes'
           id: Mapped[int] = mapped_column(primary_key=True)
           title: Mapped[str] = mapped_column(String(200))
       """)

C = "6. Django"
lesson(C, "Django: проект, приложение, URL и view",
       "Чем Django-проект отличается от Django-приложения?", "Проект объединяет настройки и конфигурацию URL. Приложение реализует отдельную область функциональности и может переиспользоваться. URLconf сопоставляет маршрут с view, которое возвращает HTTP-ответ.",
       "Напишите Django JsonResponse-view health и urlpatterns с маршрутом health/, возвращающим {'status': 'ok'}.", """
       from django.http import JsonResponse
       from django.urls import path

       def health(request):
           return JsonResponse({'status': 'ok'})

       urlpatterns = [path('health/', health, name='health')]
       """)
lesson(C, "Django ORM: модели, миграции и QuerySet",
       "Чем makemigrations отличается от migrate?", "makemigrations создаёт описание изменений моделей, migrate применяет миграции к базе. Миграции хранят в репозитории и проверяют до развёртывания; изменение models.py само по себе не изменяет схему БД.",
       "Для models.py Django-приложения напишите модель Experiment с name, created_at и необязательным accuracy; затем функцию best_experiments, возвращающую пять лучших завершённых экспериментов.", """
       from django.db import models

       class Experiment(models.Model):
           name = models.CharField(max_length=200)
           created_at = models.DateTimeField(auto_now_add=True)
           accuracy = models.FloatField(null=True, blank=True)

       def best_experiments():
           return Experiment.objects.filter(accuracy__isnull=False).order_by('-accuracy')[:5]
       """, ("Что вызывает проблему N+1 в Django ORM?", "Обращение к связанному объекту для каждой строки может делать отдельный запрос. select_related подходит для ForeignKey/OneToOne, prefetch_related — для коллекций связей и отдельных запросов с объединением результатов."))
lesson(C, "Django: формы, валидация и CSRF",
       "Что даёт Django Form при обработке POST?", "Форма преобразует входные значения, проверяет ограничения и предоставляет cleaned_data только после is_valid(). Для HTML POST-форм используется CSRF-защита; валидация браузера не заменяет проверку на сервере.",
       "Опишите TrainingForm: name до 80 символов, epochs от 1 до 500, learning_rate строго больше нуля и не больше 1.", """
       from django import forms

       class TrainingForm(forms.Form):
           name = forms.CharField(max_length=80)
           epochs = forms.IntegerField(min_value=1, max_value=500)
           learning_rate = forms.FloatField(max_value=1)

           def clean_learning_rate(self):
               value = self.cleaned_data['learning_rate']
               if value <= 0:
                   raise forms.ValidationError('Learning rate должен быть больше нуля')
               return value
       """)
lesson(C, "Django: аутентификация, права и тесты",
       "Чем проверка входа пользователя отличается от проверки доступа к объекту?", "Вход подтверждает личность, но не даёт права на все записи. Запрос к пользовательским данным ограничивают владельцем; административные действия дополнительно проверяют по разрешениям.",
       "Напишите Django view my_profile с login_required, которая возвращает id и username текущего пользователя в JSON, без пароля.", """
       from django.contrib.auth.decorators import login_required
       from django.http import JsonResponse

       @login_required
       def my_profile(request):
           return JsonResponse({'id': request.user.pk, 'username': request.user.get_username()})
       """)

C = "7. Flask"
lesson(C, "Flask: фабрика приложения и маршруты",
       "Зачем во Flask используют create_app?", "Фабрика создаёт приложение с нужной конфигурацией, подключает расширения и маршруты. Это позволяет поднимать отдельные экземпляры для тестов и разных окружений без общей изменяемой глобальной конфигурации.",
       "Напишите create_app(testing=False) для Flask с GET /health и JSON {'status': 'ok'}.", """
       from flask import Flask

       def create_app(testing=False):
           app = Flask(__name__)
           app.config['TESTING'] = testing

           @app.get('/health')
           def health():
               return {'status': 'ok'}

           return app
       """)
lesson(C, "Flask: JSON, ошибки и проверка ввода",
       "Почему Flask API должно проверять типы полей JSON?", "JSON может содержать строку вместо числа, null, список вместо объекта или отсутствующие ключи. Сервер проверяет структуру и диапазоны до вычислений и возвращает понятный клиентский код ошибки.",
       "Напишите Flask POST /square: примите JSON-объект с конечным числом x, исключая bool; иначе верните 422. Верните {'result': x*x}, проверив также конечность результата.", """
       import math
       from flask import Flask, request
       app = Flask(__name__)

       @app.post('/square')
       def square():
           data = request.get_json(silent=True)
           x = data.get('x') if isinstance(data, dict) else None
           if type(x) not in (int, float):
               return {'error': 'Нужно число x'}, 422
           try:
               result = x * x
               if not math.isfinite(x) or not math.isfinite(result):
                   raise ValueError()
           except (OverflowError, ValueError):
               return {'error': 'Число вне допустимого диапазона'}, 422
           return {'result': result}
       """)
lesson(C, "Flask: Jinja, blueprints и test_client",
       "Как проверять Flask-маршрут без запуска HTTP-сервера?", "Через app.test_client(): клиент вызывает приложение в процессе теста. Для организации растущего приложения используют blueprints, а HTML-шаблоны Jinja сохраняют автоматическое экранирование пользовательского ввода.",
       "Напишите pytest-тест test_health для create_app из модуля app: проверьте HTTP 200 и точный JSON {'status': 'ok'} через test_client.", """
       from app import create_app

       def test_health():
           app = create_app(testing=True)
           with app.test_client() as client:
               response = client.get('/health')
               assert response.status_code == 200
               assert response.get_json() == {'status': 'ok'}
       """)

C = "8. FastAPI и API для модели"
lesson(C, "FastAPI: Pydantic и схемы запросов",
       "Что проверяет модель Pydantic в FastAPI?", "Она описывает поля тела запроса, типы и ограничения, валидирует ввод и участвует в OpenAPI-схеме. Для ML важно проверить размер вектора, конечность чисел и порядок признаков.",
       "Создайте FastAPI POST /validate с телом Features: values — ровно четыре конечных float; верните проверенные значения.", """
       from fastapi import FastAPI
       from pydantic import BaseModel, Field, FiniteFloat

       class Features(BaseModel):
           values: list[FiniteFloat] = Field(min_length=4, max_length=4)

       app = FastAPI()

       @app.post('/validate')
       def validate(body: Features):
           return {'values': body.values}
       """)
lesson(C, "FastAPI: зависимости и жизненный цикл ресурсов",
       "Почему модель обычно не загружают с диска на каждом API-запросе?", "Загрузка весов расходует время и память. Общий ресурс загружают при старте процесса через lifespan, а обработчикам предоставляют через состояние приложения или зависимости. Ресурсы закрывают при завершении.",
       "Напишите lifespan для FastAPI, который сохраняет результат load_model() из model_service в app.state.model при старте и удаляет ссылку при остановке.", """
       from contextlib import asynccontextmanager
       from fastapi import FastAPI
       from model_service import load_model

       @asynccontextmanager
       async def lifespan(app):
           app.state.model = load_model()
           try:
               yield
           finally:
               del app.state.model

       app = FastAPI(lifespan=lifespan)
       """)
lesson(C, "FastAPI: тестирование контрактов",
       "Что следует проверить у API предсказаний кроме ответа 200?", "Формат результата, число классов, невалидные типы, пропущенные и лишние признаки, NaN/Inf и поведение при отсутствии модели. Предсказания проверяют на известном небольшом примере.",
       "Для приложения app с маршрутом /validate напишите TestClient-тест: четыре числа принимаются, три числа дают 422.", """
       from fastapi.testclient import TestClient
       from app import app

       def test_features_contract():
           with TestClient(app) as client:
               assert client.post('/validate', json={'values': [1, 2, 3, 4]}).status_code == 200
               assert client.post('/validate', json={'values': [1, 2, 3]}).status_code == 422
       """)

C = "9. tkinter и настольные приложения"
lesson(C, "tkinter: окно, ttk, grid и события",
       "Зачем tkinter нужен mainloop?", "Цикл событий обрабатывает ввод, перерисовку и запланированные callbacks. Обработчики должны быстро возвращать управление. ttk предоставляет виджеты с тематическим оформлением.",
       "Создайте окно tkinter с ttk.Label и ttk.Button в grid. Кнопка меняет подпись метки на 'Готово'. Запуск — под защитой __main__.", """
       import tkinter as tk
       from tkinter import ttk

       def main():
           root = tk.Tk()
           root.title('Первое приложение')
           label = ttk.Label(root, text='Ожидание')
           label.grid(row=0, column=0, padx=12, pady=12)
           ttk.Button(root, text='Начать', command=lambda: label.config(text='Готово')).grid(row=1, column=0)
           root.mainloop()

       if __name__ == '__main__':
           main()
       """)
lesson(C, "tkinter: формы и валидация значений",
       "Где проверять значения Entry перед вызовом модели?", "В обработчике действия: строку преобразуют в число, проверяют диапазон и конечность. При ошибке показывают понятное сообщение и не запускают вычисление; нельзя полагаться только на фильтрацию клавиш.",
       "Напишите read_features(entries) для списка из четырёх Entry: верните четыре конечных float; при ошибке покажите messagebox.showerror и верните None.", """
       import math
       from tkinter import messagebox

       def read_features(entries):
           try:
               values = [float(entry.get()) for entry in entries]
               if len(values) != 4 or not all(math.isfinite(x) for x in values):
                   raise ValueError()
               return values
           except ValueError:
               messagebox.showerror('Ошибка ввода', 'Введите четыре конечных числа')
               return None
       """)
lesson(C, "tkinter: Treeview и выбор файлов",
       "Для чего удобен ttk.Treeview в приложении анализа данных?", "Он показывает строки с несколькими колонками и поддерживает выбор элементов. Для больших таблиц отображают ограниченную выборку или страницы, чтобы не блокировать интерфейс вставкой миллионов строк.",
       "Напишите fill_table(tree, rows): очистите Treeview и добавьте максимум 100 строк словарей с полями epoch и loss.", """
       def fill_table(tree, rows):
           for item in tree.get_children():
               tree.delete(item)
           for row in rows[:100]:
               tree.insert('', 'end', values=(row['epoch'], f\"{row['loss']:.4f}\"))
       """)
lesson(C, "tkinter: обучение в фоне и очередь сообщений",
       "Как показать прогресс долгой задачи и не заморозить tkinter?", "Работу выносят из GUI-обработчика, сообщения передают через queue.Queue. Главный поток читает очередь через root.after и обновляет виджеты; рабочий поток не обращается к виджетам напрямую.",
       "Напишите poll_progress(root, label, messages), читающую Queue через get_nowait, обновляющую label и планирующую себя снова через after(100).",
       """
       from queue import Empty

       def poll_progress(root, label, messages):
           try:
               while True:
                   label.config(text=str(messages.get_nowait()))
           except Empty:
               pass
           root.after(100, poll_progress, root, label, messages)
       """)

C = "10. NumPy"
lesson(C, "NumPy: массивы, shape и dtype",
       "Почему для нейросети проверяют shape и dtype массива?", "Shape задаёт количество объектов и признаков; перепутанные оси меняют смысл вычислений. Float32 часто используется для входов модели, а метки классов — целочисленные. Строковые и object-массивы нужно преобразовать до обучения.",
       "Напишите as_features(rows): преобразуйте данные в np.float32, проверьте двумерность и четыре столбца, а также отсутствие NaN/Inf.", """
       import numpy as np

       def as_features(rows):
           x = np.asarray(rows, dtype=np.float32)
           if x.ndim != 2 or x.shape[1] != 4 or not np.isfinite(x).all():
               raise ValueError('Нужна конечная матрица N x 4')
           return x
       """)
lesson(C, "NumPy: broadcasting и векторизация",
       "Когда NumPy может применить broadcasting?", "Размеры сравниваются с конца: по каждой оси они должны совпадать либо один размер равен 1; отсутствующая ось считается единичной. Вектор из D значений можно вычесть из матрицы N×D построчно.",
       "Напишите center_columns(x), вычитающую из каждого столбца его среднее без циклов. x — непустая двумерная матрица чисел.", """
       import numpy as np

       def center_columns(x):
           x = np.asarray(x, dtype=float)
           return x - x.mean(axis=0, keepdims=True)
       """)
lesson(C, "NumPy: индексация и статистики",
       "Что делает булева маска при выборе строк массива?", "Маска той же длины, что первая ось, выбирает строки с True. Она удобна для фильтрации невалидных объектов и подмножеств; нужно одновременно сохранять соответствие между признаками и метками.",
       "Напишите finite_rows(x, y): удалите строки x с NaN/Inf и те же элементы y; верните пару массивов.", """
       import numpy as np

       def finite_rows(x, y):
           x, y = np.asarray(x), np.asarray(y)
           mask = np.isfinite(x).all(axis=1)
           return x[mask], y[mask]
       """)

C = "11. pandas"
lesson(C, "pandas: DataFrame, CSV и выбор столбцов",
       "Как проверить таблицу сразу после read_csv?", "Посмотреть head, shape, dtypes и количество пропусков, проверить названия обязательных колонок и диапазоны значений. Числа могут прочитаться как строки из-за формата исходных данных.",
       "Напишите load_table(path): прочитайте CSV, потребуйте столбцы age и income и верните только эти столбцы в данном порядке.", """
       import pandas as pd

       def load_table(path):
           frame = pd.read_csv(path)
           required = ['age', 'income']
           if not set(required) <= set(frame.columns):
               raise ValueError('Нужны столбцы age и income')
           return frame.loc[:, required].copy()
       """)
lesson(C, "pandas: пропуски, дубликаты и типы",
       "Почему заполнение пропусков медианой всего датасета может дать утечку?", "Медиана будет учитывать validation/test. Сначала данные делят, затем обучают преобразование на train и применяют его без переобучения к остальным частям. Простое удаление дубликатов также требует понимания того, что считать независимым наблюдением.",
       "Напишите clean_amount(frame): верните копию с amount, преобразованным через to_numeric(errors='coerce'), и без строк с пропущенным amount. Остальные столбцы сохраните.", """
       import pandas as pd

       def clean_amount(frame):
           result = frame.copy()
           result['amount'] = pd.to_numeric(result['amount'], errors='coerce')
           return result.dropna(subset=['amount'])
       """)
lesson(C, "pandas: groupby, фильтрация и агрегирование",
       "Чем агрегирование groupby отличается от transform?", "Агрегирование сводит группу к одному или нескольким итогам. Transform возвращает значения, выровненные с исходными строками, например среднее группы для каждого объекта.",
       "По DataFrame продаж с region и amount напишите revenue_by_region(frame), возвращающую суммы по регионам по убыванию.", """
       def revenue_by_region(frame):
           return frame.groupby('region', as_index=False)['amount'].sum().sort_values('amount', ascending=False)
       """)
lesson(C, "pandas: merge и контроль объединений",
       "Как merge может неожиданно увеличить число строк?", "Повторяющийся ключ с обеих сторон создаёт комбинации строк. Параметр validate проверяет ожидаемую кардинальность; indicator помогает обнаружить несопоставленные ключи.",
       "Напишите attach_customers(orders, customers): левое объединение по customer_id с проверкой many-to-one и колонкой-индикатором.", """
       def attach_customers(orders, customers):
           return orders.merge(customers, on='customer_id', how='left', validate='many_to_one', indicator=True)
       """)

C = "12. Анализ и визуализация"
lesson(C, "matplotlib: графики данных и ошибок обучения",
       "Зачем на одном графике смотреть train loss и validation loss?", "Снижение train loss при росте validation loss может указывать на переобучение. Сравнивать надо одинаково рассчитанные метрики; по одному графику нельзя исключить ошибки подготовки данных.",
       "Напишите plot_history(history, path): постройте train_loss и val_loss по epoch через matplotlib, подпишите оси, добавьте легенду, сохраните рисунок и закройте figure.", """
       import matplotlib.pyplot as plt

       def plot_history(history, path):
           fig, ax = plt.subplots()
           epochs = [row['epoch'] for row in history]
           for name in ('train_loss', 'val_loss'):
               ax.plot(epochs, [row[name] for row in history], label=name)
           ax.set(xlabel='Epoch', ylabel='Loss')
           ax.legend()
           fig.savefig(path)
           plt.close(fig)
       """)
lesson(C, "Jupyter и воспроизводимый эксперимент",
       "Почему notebook может работать только при определённом порядке запуска ячеек?", "Ядро сохраняет состояние, включая старые переменные и объекты. Проверка Restart and Run All обнаруживает скрытые зависимости; итоговый эксперимент лучше оформлять функциями и запускать скриптом с записанными параметрами.",
       "Напишите save_config(path, seed, epochs), сохраняющую параметры и версию Python в UTF-8 JSON.", """
       import json
       import platform
       from pathlib import Path

       def save_config(path, seed, epochs):
           data = {'seed': seed, 'epochs': epochs, 'python': platform.python_version()}
           Path(path).write_text(json.dumps(data, indent=2), encoding='utf-8')
       """)

C = "13. Машинное обучение со scikit-learn"
lesson(C, "Признаки, целевая переменная и разбиение данных",
       "Чем train, validation и test отличаются по назначению?", "Train используется для обучения параметров, validation — для выбора настроек, test — для финальной оценки. Для временных рядов разделяют по времени, а связанные наблюдения — по группам, чтобы избежать утечки.",
       "Напишите split_data(x, y): стратифицированно разделите классификационные данные на 60% train, 20% validation, 20% test с random_state=42. Верните три пары (X, y).", """
       from sklearn.model_selection import train_test_split

       def split_data(x, y):
           xp, xt, yp, yt = train_test_split(x, y, test_size=0.2, stratify=y, random_state=42)
           xr, xv, yr, yv = train_test_split(xp, yp, test_size=0.25, stratify=yp, random_state=42)
           return (xr, yr), (xv, yv), (xt, yt)
       """)
lesson(C, "StandardScaler, Pipeline и защита от утечки",
       "Почему Pipeline полезен при кросс-валидации?", "Он объединяет preprocessing и модель. При корректной кросс-валидации всего Pipeline преобразования обучаются только на обучающей части каждого фолда, а не на всей выборке заранее.",
       "Создайте и обучите на x_train, y_train Pipeline из StandardScaler и LogisticRegression(max_iter=1000). Верните pipeline.", """
       from sklearn.pipeline import make_pipeline
       from sklearn.preprocessing import StandardScaler
       from sklearn.linear_model import LogisticRegression

       def fit_baseline(x_train, y_train):
           pipeline = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))
           return pipeline.fit(x_train, y_train)
       """)
lesson(C, "Метрики: accuracy, precision, recall и F1",
       "Почему высокая accuracy может быть бесполезной при дисбалансе?", "Если один класс встречается в 99% случаев, постоянный ответ этим классом даст 99% accuracy. Смотрят матрицу ошибок, precision/recall и F1 по классам и выбирают метрику по цене ошибок.",
       "Напишите classification_metrics(y_true, y_pred): верните accuracy, macro F1 с zero_division=0 и confusion_matrix как список списков.", """
       from sklearn.metrics import accuracy_score, f1_score, confusion_matrix

       def classification_metrics(y_true, y_pred):
           return {'accuracy': accuracy_score(y_true, y_pred),
                   'f1_macro': f1_score(y_true, y_pred, average='macro', zero_division=0),
                   'confusion_matrix': confusion_matrix(y_true, y_pred).tolist()}
       """)
lesson(C, "Baseline, переобучение и выбор модели",
       "Зачем сравнивать нейросеть с простой baseline-моделью?", "Так проверяют, даёт ли сложность реальный выигрыш. Baseline может быть постоянным классом или линейной моделью. Улучшения сначала оценивают на validation, а test не используют для многократного подбора настроек.",
       "Напишите dummy_accuracy(x_train, y_train, x_val, y_val): обучите DummyClassifier(strategy='most_frequent') и верните accuracy на validation.", """
       from sklearn.dummy import DummyClassifier

       def dummy_accuracy(x_train, y_train, x_val, y_val):
           model = DummyClassifier(strategy='most_frequent').fit(x_train, y_train)
           return model.score(x_val, y_val)
       """)

C = "14. PyTorch с нуля"
lesson(C, "PyTorch: тензоры, dtype, shape и CPU",
       "Какие типы нужны для признаков и целочисленных меток в CrossEntropyLoss?", "Признаки и logits обычно float32, метки индексов классов — torch.long. Logits имеют форму [N, C], метки — [N] со значениями от 0 до C−1. Все участвующие тензоры должны находиться на совместимом устройстве.",
       "Напишите to_tensors(x, y), создающую на CPU признаки float32 и метки long.", """
       import torch

       def to_tensors(x, y):
           return torch.tensor(x, dtype=torch.float32), torch.tensor(y, dtype=torch.long)
       """)
lesson(C, "PyTorch: autograd и backward",
       "Что делает backward и почему градиенты обнуляют?", "Backward вычисляет производные loss по обучаемым параметрам и накапливает их в .grad. Если не обнулить их перед новым независимым шагом, градиенты сложатся с предыдущими; намеренное накопление — отдельная техника.",
       "Создайте скаляр x=3.0 с requires_grad=True, вычислите y=x*x, вызовите backward и верните значение градиента в функции square_gradient().", """
       import torch

       def square_gradient():
           x = torch.tensor(3.0, requires_grad=True)
           (x * x).backward()
           return x.grad.item()
       """)
lesson(C, "PyTorch: nn.Module, Linear и ReLU",
       "Почему сеть из нескольких Linear без нелинейности ограничена?", "Композиция аффинных преобразований остаётся аффинным преобразованием. ReLU между слоями позволяет моделировать нелинейные зависимости; число выходов последнего слоя выбирают по задаче.",
       "Напишите make_model(): сеть для четырёх признаков и трёх классов с одним скрытым слоем из 16 нейронов и ReLU, без Softmax на выходе.", """
       from torch import nn

       def make_model():
           return nn.Sequential(nn.Linear(4, 16), nn.ReLU(), nn.Linear(16, 3))
       """)
lesson(C, "PyTorch: TensorDataset и DataLoader",
       "Что дают batch_size и shuffle в DataLoader?", "Batch size задаёт число объектов в шаге оптимизации, shuffle меняет порядок обучающих примеров. Для validation/test перемешивание обычно не требуется. На Windows простой учебный пример удобно начать с num_workers=0.",
       "Напишите make_loader(x_tensor, y_tensor): TensorDataset и DataLoader с batch_size=16, shuffle=True, num_workers=0 и генератором с seed=42.", """
       import torch
       from torch.utils.data import TensorDataset, DataLoader

       def make_loader(x_tensor, y_tensor):
           return DataLoader(TensorDataset(x_tensor, y_tensor), batch_size=16, shuffle=True,
                             num_workers=0, generator=torch.Generator().manual_seed(42))
       """)

C = "15. Обучение и сохранение нейросети"
lesson(C, "PyTorch: функция потерь и шаг оптимизации",
       "Почему перед CrossEntropyLoss не нужно применять Softmax?", "Для целочисленных меток CrossEntropyLoss принимает необработанные logits и сама выполняет нужное преобразование. Предварительный Softmax меняет вход функции потерь и ухудшает численную схему обучения.",
       "Напишите train_step(model, optimizer, x, y): train, zero_grad, logits, CrossEntropyLoss, backward, step; верните loss как число.", """
       from torch import nn

       def train_step(model, optimizer, x, y):
           model.train()
           optimizer.zero_grad()
           loss = nn.CrossEntropyLoss()(model(x), y)
           loss.backward()
           optimizer.step()
           return loss.item()
       """)
lesson(C, "PyTorch: эпохи и средняя ошибка",
       "Как правильно усреднить loss по эпохе при неполном последнем батче?", "Если loss усреднён внутри батча, его умножают на размер батча, суммируют и делят на число всех объектов. Среднее средних без весов переоценивает маленький последний батч.",
       "Напишите train_epoch(model, loader, optimizer), обучающую одну эпоху с CrossEntropyLoss и возвращающую среднюю ошибку на объект. При пустом loader поднимите ValueError.", """
       from torch import nn

       def train_epoch(model, loader, optimizer):
           model.train()
           loss_fn = nn.CrossEntropyLoss()
           total, count = 0.0, 0
           for x, y in loader:
               optimizer.zero_grad()
               loss = loss_fn(model(x), y)
               loss.backward()
               optimizer.step()
               total += loss.item() * len(y)
               count += len(y)
           if count == 0:
               raise ValueError('Пустая обучающая выборка')
           return total / count
       """)
lesson(C, "PyTorch: eval, inference_mode и валидация",
       "Чем model.eval() отличается от torch.inference_mode()?", "Eval переключает поведение слоёв, например Dropout и BatchNorm, но не отключает autograd. Inference mode отключает запись графа и дополнительные накладные расходы; он сам не переводит модель в eval.",
       "Напишите accuracy(model, x, y), использующую eval и inference_mode, argmax по классам и возвращающую долю верных ответов.", """
       import torch

       def accuracy(model, x, y):
           model.eval()
           with torch.inference_mode():
               predicted = model(x).argmax(dim=1)
               return (predicted == y).float().mean().item()
       """)
lesson(C, "PyTorch: learning rate, seed и лучшие веса",
       "Почему best_state = model.state_dict() недостаточно для сохранения лучшей эпохи в памяти?", "Словарь содержит ссылки на тензоры параметров, которые продолжат изменяться при обучении. Для снимка используют deepcopy или detached clone каждого тензора. Лучшие веса выбирают по validation, а не по test.",
       "Напишите snapshot(model), возвращающую независимую копию state_dict на CPU с detach().clone().",
       """
       def snapshot(model):
           return {name: value.detach().cpu().clone() for name, value in model.state_dict().items()}
       """)
lesson(C, "PyTorch: state_dict и загрузка для предсказания",
       "Что кроме весов нужно сохранить для корректного предсказания?", "Архитектуру или её конфигурацию, порядок признаков, параметры preprocessing и соответствие индексов названиям классов. При загрузке создают ту же архитектуру, загружают state_dict и вызывают eval; для собственных тензорных checkpoints используют weights_only=True.",
       "Напишите load_weights(path, make_model): загрузите state_dict на CPU через weights_only=True, примените его к созданной модели, включите eval и верните модель.", """
       import torch

       def load_weights(path, make_model):
           model = make_model()
           model.load_state_dict(torch.load(path, map_location='cpu', weights_only=True))
           model.eval()
           return model
       """)

C = "16. Качество и выпуск приложения"
lesson(C, "pytest: параметризация и граничные случаи",
       "Какие тесты нужны для функции подготовки признаков?", "Корректные данные, неверное число признаков, неправильный тип, NaN/Inf и совпадение preprocessing при обучении и предсказании. Тестам вычислений задают допустимую погрешность вместо точного равенства float.",
       "Напишите параметризованный pytest-тест для parse_port из utils: строки '0', '65536', 'abc' должны вызывать ValueError.", """
       import pytest
       from utils import parse_port

       @pytest.mark.parametrize('text', ['0', '65536', 'abc'])
       def test_invalid_port(text):
           with pytest.raises(ValueError):
               parse_port(text)
       """)
lesson(C, "Логирование, конфигурация и секреты",
       "Что записывать в журнал обучения?", "Параметры запуска, размеры выборок, seed, версии библиотек, ошибки по эпохам и путь к артефактам. Пароли, токены и персональные данные в лог не помещают; конфигурацию среды читают отдельно от исходного кода.",
       "Настройте logging на INFO и напишите log_epoch(epoch, train_loss, val_loss) с форматированием чисел до четырёх знаков через параметры logger.info.", """
       import logging
       logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
       logger = logging.getLogger(__name__)

       def log_epoch(epoch, train_loss, val_loss):
           logger.info('epoch=%d train_loss=%.4f val_loss=%.4f', epoch, train_loss, val_loss)
       """)
lesson(C, "Упаковка, Docker и запуск сервиса",
       "Что следует отделить от кода при упаковке приложения с моделью?", "Зависимости и конфигурацию запуска фиксируют отдельно; артефакт модели версионируют и передают как файл или том. Обучение не запускают при каждом старте API. Для веб-сервиса выбирают подходящий production-сервер вместо debug-сервера.",
       "Напишите model_path(), читающую MODEL_PATH из окружения (по умолчанию data/model.pt), проверяющую существование файла и возвращающую Path.", """
       import os
       from pathlib import Path

       def model_path():
           path = Path(os.environ.get('MODEL_PATH', 'data/model.pt'))
           if not path.is_file():
               raise FileNotFoundError(f'Модель не найдена: {path}')
           return path
       """)

C = "17. Итоговый проект: первая нейросеть"
lesson(C, "Проект Iris: полный цикл обучения на CPU",
       "Какие результаты должен выдавать завершённый учебный проект обучения?", "Воспроизводимый запуск, разделённые train/validation/test, график обучения, сравнение с baseline, итоговую метрику на test, сохранённую модель с preprocessing и отдельный сценарий предсказания.",
       "Соберите программу обучения классификатора Iris на CPU: 4→16→3, train/validation/test 60/20/20, StandardScaler только на train, Adam, CrossEntropyLoss, выбор лучших весов по validation loss, итоговые test accuracy и confusion matrix. Сохраните checkpoint и историю; добавьте CLI для обучения и предсказания. Датасет возьмите из sklearn.datasets.load_iris. Эталон также находится в examples/python_neural_network/train.py.",
       (Path(__file__).resolve().parents[2] / "examples/python_neural_network/train.py").read_text(encoding="utf-8"))
lesson(C, "Проект Iris: предсказание из сохранённой модели",
       "Почему нельзя заново обучать StandardScaler на одном новом цветке?", "Модель обучена в пространстве признаков, заданном статистиками train. Новые данные преобразуют теми же сохранёнными mean и scale и в том же порядке колонок; новый fit изменит смысл входов.",
       "Напишите normalize_one(values, mean, scale): проверьте, что каждый вектор содержит четыре конечных числа, scale положителен, затем верните нормализованный np.float32 массив формы (1,4).", """
       import numpy as np

       def normalize_one(values, mean, scale):
           values, mean, scale = (np.asarray(v, dtype=np.float32) for v in (values, mean, scale))
           if any(v.shape != (4,) or not np.isfinite(v).all() for v in (values, mean, scale)) or (scale <= 0).any():
               raise ValueError('Неверные признаки или параметры нормализации')
           return ((values - mean) / scale).reshape(1, 4)
       """)
lesson(C, "Проект Iris: интерфейс предсказаний",
       "Как разделить обучение, инференс и интерфейс приложения?", "Обучение сохраняет артефакты отдельной командой, модуль инференса загружает модель и преобразует вход, а API или GUI отвечает за ввод и представление результата. Это позволяет тестировать части независимо и менять интерфейс без повторного обучения.",
       "В модуле iris_api.py создайте FastAPI POST /predict. Предположите, что model_service.predict_values(values) уже загружает и использует модель; валидируйте четыре конечных числа через Pydantic и верните результат сервиса.", """
       from fastapi import FastAPI
       from pydantic import BaseModel, Field, FiniteFloat
       from model_service import predict_values

       class Input(BaseModel):
           values: list[FiniteFloat] = Field(min_length=4, max_length=4)

       app = FastAPI()

       @app.post('/predict')
       def predict(body: Input):
           return predict_values(body.values)
       """)

TRACK = {
    "id": "python",
    "title": "Python-разработчик",
    "description": "От основ Python до приложений на Django, Flask, FastAPI и tkinter; NumPy, pandas, scikit-learn и первая нейросеть на PyTorch.",
    "icon": "python",
    "language": "python",
    "related": ["python-basics.json", "python-live-coding.json", "ttk-widgets.json", "pytorch-basics.json"],
    "subjects": ["Python и ООП", "Django", "Flask", "FastAPI", "tkinter", "SQLAlchemy", "NumPy и pandas", "matplotlib и Jupyter", "scikit-learn", "PyTorch: первая нейросеть", "Тестирование и выпуск"],
    "syllabus": {"id": "pro_python", "chapters": CHAPTERS},
    "theory": THEORY,
    "practice": PRACTICE,
}
