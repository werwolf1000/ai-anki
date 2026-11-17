# Первая нейросеть на Python

Итоговый проект профессии «Python-разработчик»: небольшая сеть определяет вид ириса по четырём
измерениям цветка. Датасет Iris входит в scikit-learn; после установки зависимостей интернет и GPU
не нужны. Ориентир — Python 3.12 в отдельном виртуальном окружении.

Из корня репозитория:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r examples/python_neural_network/requirements.txt
python examples/python_neural_network/train.py --epochs 100
python examples/python_neural_network/train.py --predict 5.1 3.5 1.4 0.2
```

В Linux/macOS окружение активируется командой `source .venv/bin/activate`.
Для другой платформы способ установки PyTorch можно выбрать в [официальной инструкции](https://pytorch.org/get-started/locally/).

## Что происходит в программе

1. Данные загружаются в pandas DataFrame и преобразуются в массивы NumPy.
2. Делятся на 90 обучающих, 30 валидационных и 30 тестовых примеров со стратификацией.
3. `StandardScaler` обучается только на train; его параметры применяются к validation и test.
4. Сеть `4 → 16 → 3` обучается на CPU мини-батчами с Adam и CrossEntropyLoss.
5. Лучшая эпоха выбирается по validation loss. Test используется один раз для итогового отчёта.
6. Сохраняются веса, параметры нормализации, названия признаков и классов. Отдельный запуск загружает
   модель и предсказывает класс нового цветка.

В `data/python-neural-network/` появятся `model.pt`, `metrics.json`, `history.json`, `iris.csv`.
`test_accuracy` сравнивается с простой моделью, всегда выдающей наиболее частый класс.
Маленький учебный test не доказывает готовность модели к реальным данным: при изменении задачи
нужны собственные данные и отдельная оценка качества.

## Как пройти проект самостоятельно

- Воспроизведите загрузку, разделение данных и нормализацию.
- Напишите модель и один шаг обучения, затем полный цикл.
- Постройте графики train/validation loss по `history.json` с matplotlib.
- Поменяйте число скрытых нейронов и learning rate; сравнивайте варианты на validation.
- Вынесите загрузку модели и предсказание в модуль; добавьте FastAPI-эндпоинт либо форму tkinter.
- Добавьте проверки количества признаков, NaN и повторяемости предсказаний после загрузки.

Контрольные вопросы: почему нельзя нормализовать весь датасет перед разбиением, зачем обнулять
градиенты, почему перед CrossEntropyLoss нет Softmax, чем `eval()` отличается от `inference_mode()`?

Основа работы с моделью описана в [PyTorch Learn the Basics](https://docs.pytorch.org/tutorials/beginner/basics/quickstart_tutorial.html)
и [руководстве по сохранению весов](https://docs.pytorch.org/tutorials/beginner/basics/saveloadrun_tutorial.html).
Правила подготовки данных — в [scikit-learn: common pitfalls](https://scikit-learn.org/stable/common_pitfalls.html).
