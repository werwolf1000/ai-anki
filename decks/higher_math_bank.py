from __future__ import annotations

from math_card import math

TOPIC_DERIV = "Производные"
TOPIC_INTEGR = "Интегралы"
TOPIC_LIMITS = "Пределы"
TOPIC_SERIES = "Ряды и приближения"
TOPIC_MATRICES = "Матрицы"
TOPIC_LINEAR = "Линейная алгебра"
TOPIC_VECTORS = "Векторы"
TOPIC_MULTIVAR = "Многомерный анализ"


def _derivatives() -> list[dict]:
    cards: list[dict] = []
    power = [
        ("x^2", "2x"),
        ("x^3", "3x^2"),
        ("x^5", "5x^4"),
        ("x^{-1}", "-x^{-2}"),
        ("x^{-2}", "-2x^{-3}"),
        ("\\sqrt{x}", "\\frac{1}{2\\sqrt{x}}"),
        ("x^{1/3}", "\\frac{1}{3}x^{-2/3}"),
    ]
    for f, fp in power:
        cards.append(math(f"Найдите $f'(x)$, если $f(x)={f}$.", f"f'(x)={fp}", topic=TOPIC_DERIV))

    product = [
        ("x^2 \\sin x", "2x \\sin x + x^2 \\cos x"),
        ("x e^x", "e^x(x+1)"),
        ("x \\ln x", "\\ln x + 1"),
        ("x^2 \\cos x", "2x \\cos x - x^2 \\sin x"),
        ("e^x \\sin x", "e^x(\\sin x + \\cos x)"),
    ]
    for f, fp in product:
        cards.append(math(f"Найдите производную $f(x)={f}$.", f"f'(x)={fp}", topic=TOPIC_DERIV))

    chain = [
        ("\\ln(x^2+1)", "\\frac{2x}{x^2+1}"),
        ("\\ln(\\cos x)", "-\\tan x"),
        ("e^{x^2}", "2x e^{x^2}"),
        ("\\sin(x^2)", "2x \\cos(x^2)"),
        ("\\cos(3x)", "-3\\sin(3x)"),
        ("\\sin^2 x", "\\sin(2x)"),
        ("(x^2+1)^5", "10x(x^2+1)^4"),
        ("\\sqrt{x^2+4}", "\\frac{x}{\\sqrt{x^2+4}}"),
    ]
    for f, fp in chain:
        cards.append(
            math(f"Найдите $\\frac{{d}}{{dx}}\\left({f}\\right)$.", f"\\frac{{d}}{{dx}}({f})={fp}", topic=TOPIC_DERIV)
        )

    basic = [
        ("\\sin x", "\\cos x"),
        ("\\cos x", "-\\sin x"),
        ("\\tan x", "\\frac{1}{\\cos^2 x}"),
        ("e^x", "e^x"),
        ("a^x", "a^x \\ln a"),
        ("\\arctan x", "\\frac{1}{1+x^2}"),
        ("\\arcsin x", "\\frac{1}{\\sqrt{1-x^2}}"),
        ("\\operatorname{sh} x", "\\operatorname{ch} x"),
    ]
    for f, fp in basic:
        cards.append(math(f"Найдите $\\frac{{d}}{{dx}}({f})$.", f"\\frac{{d}}{{dx}}({f})={fp}", topic=TOPIC_DERIV))

    higher = [
        ("x^4 - 3x^2", "4x^3 - 6x"),
        ("x^3 - 6x^2 + 5", "3x^2 - 12x"),
        ("\\sin x + \\cos x", "\\cos x - \\sin x"),
        ("e^x + x e^x", "e^x(2+x)"),
        ("\\frac{x}{x+1}", "\\frac{1}{(x+1)^2}"),
        ("\\frac{1}{x^2+1}", "\\frac{-2x}{(x^2+1)^2}"),
    ]
    for f, fp in higher:
        cards.append(math(f"Найдите $f''(x)$ для $f(x)={f}$.", f"f''(x)={fp}", topic=TOPIC_DERIV))

    cards.extend([
        math(
            "Запишите уравнение касательной к $y=x^2$ в точке $x=1$.",
            "y - 1 = 2(x - 1) \\;\\Rightarrow\\; y = 2x - 1",
            topic=TOPIC_DERIV,
        ),
        math(
            "Запишите уравнение касательной к $y=\\ln x$ в точке $x=1$.",
            "y = x - 1",
            topic=TOPIC_DERIV,
        ),
        math(
            "Найдите $f'(2)$, если $f(x)=x^3-x$.",
            "f'(x)=3x^2-1,\\quad f'(2)=11",
            topic=TOPIC_DERIV,
        ),
        math(
            "Найдите производную $y=|x|$ в точках $x>0$ и $x<0$.",
            "y'=1\\ (x>0),\\quad y'=-1\\ (x<0)",
            topic=TOPIC_DERIV,
        ),
        math(
            "Найдите $dy/dx$, если $x^2+y^2=25$ (неявное дифференцирование).",
            "\\frac{dy}{dx}=-\\frac{x}{y}",
            topic=TOPIC_DERIV,
        ),
        math(
            "Найдите $dy/dx$, если $e^{xy}=x+y$.",
            "\\frac{dy}{dx}=\\frac{1-ye^{xy}}{xe^{xy}-1}",
            topic=TOPIC_DERIV,
        ),
        math(
            "Найдите $f'(x)$ для $f(x)=x^x$ при $x>0$.",
            "f'(x)=x^x(\\ln x + 1)",
            topic=TOPIC_DERIV,
        ),
        math(
            "Найдите точки экстремума $f(x)=x^3-3x$.",
            "f'(x)=3x^2-3=0 \\Rightarrow x=\\pm1;\\; x=-1\\ —\\ макс.,\\; x=1\\ —\\ мин.",
            topic=TOPIC_DERIV,
        ),
    ])
    return cards


def _integrals() -> list[dict]:
    cards: list[dict] = []
    basic = [
        ("x", "\\frac{x^2}{2}+C"),
        ("x^2", "\\frac{x^3}{3}+C"),
        ("x^3", "\\frac{x^4}{4}+C"),
        ("\\frac{1}{x}", "\\ln|x|+C"),
        ("\\cos x", "\\sin x+C"),
        ("\\sin x", "-\\cos x+C"),
        ("e^x", "e^x+C"),
        ("a^x", "\\frac{a^x}{\\ln a}+C"),
        ("\\sec^2 x", "\\tan x+C"),
        ("\\frac{1}{\\cos^2 x}", "\\tan x+C"),
    ]
    for f, F in basic:
        cards.append(
            math(f"Вычислите $\\displaystyle \\int {f}\\,dx$.", f"\\int {f}\\,dx = {F}", topic=TOPIC_INTEGR)
        )

    sub = [
        ("2x e^{x^2}", "e^{x^2}+C"),
        ("\\frac{2x}{x^2+1}", "\\ln(x^2+1)+C"),
        ("\\frac{1}{2\\sqrt{x}}", "\\sqrt{x}+C"),
        ("x\\sqrt{x^2+1}", "\\frac{(x^2+1)^{3/2}}{3}+C"),
        ("\\frac{\\ln x}{x}", "\\frac{(\\ln x)^2}{2}+C"),
        ("\\sin x \\cos x", "-\\frac{\\cos^2 x}{2}+C"),
        ("\\frac{e^x}{e^x+1}", "\\ln(e^x+1)+C"),
    ]
    for f, F in sub:
        cards.append(
            math(f"Вычислите $\\displaystyle \\int {f}\\,dx$ (замена переменной).", f"\\int {f}\\,dx = {F}", topic=TOPIC_INTEGR)
        )

    parts = [
        ("x e^x", "e^x(x-1)+C"),
        ("x \\sin x", "\\sin x - x\\cos x + C"),
        ("x \\cos x", "x\\sin x + \\cos x + C"),
        ("\\ln x", "x\\ln x - x + C"),
        ("x \\ln x", "\\frac{x^2}{2}\\ln x - \\frac{x^2}{4}+C"),
        ("x^2 e^x", "e^x(x^2-2x+2)+C"),
    ]
    for f, F in parts:
        cards.append(
            math(f"Вычислите $\\displaystyle \\int {f}\\,dx$ (по частям).", f"\\int {f}\\,dx = {F}", topic=TOPIC_INTEGR)
        )

    definite = [
        ("x^2", "0", "1", "\\frac{1}{3}"),
        ("x", "0", "2", "2"),
        ("\\cos x", "0", "\\pi/2", "1"),
        ("\\sin x", "0", "\\pi", "2"),
        ("e^x", "0", "1", "e-1"),
        ("\\frac{1}{x}", "1", "e", "1"),
        ("x^3", "-1", "1", "0"),
        ("|x|", "-1", "1", "1"),
        ("\\sqrt{1-x^2}", "0", "1", "\\frac{\\pi}{4}"),
    ]
    for f, a, b, val in definite:
        cards.append(
            math(
                f"Вычислите $\\displaystyle \\int_{a}^{b} {f}\\,dx$.",
                f"\\int_{a}^{b} {f}\\,dx = {val}",
                topic=TOPIC_INTEGR,
            )
        )

    cards.extend([
        math(
            "Найдите площадь под графиком $y=x$ на $[0,3]$.",
            "S=\\int_0^3 x\\,dx = \\frac{9}{2}",
            topic=TOPIC_INTEGR,
        ),
        math(
            "Найдите объём тела вращения $y=x^2$ вокруг $Ox$ на $[0,1]$.",
            "V=\\pi\\int_0^1 x^4\\,dx = \\frac{\\pi}{5}",
            topic=TOPIC_INTEGR,
        ),
        math(
            "Вычислите $\\displaystyle \\int \\frac{1}{x^2+4}\\,dx$.",
            "\\int \\frac{1}{x^2+4}\\,dx = \\frac{1}{2}\\arctan\\frac{x}{2}+C",
            topic=TOPIC_INTEGR,
        ),
        math(
            "Вычислите $\\displaystyle \\int \\frac{1}{\\sqrt{1-x^2}}\\,dx$.",
            "\\arcsin x + C",
            topic=TOPIC_INTEGR,
        ),
        math(
            "Вычислите $\\displaystyle \\int \\frac{1}{1+x^2}\\,dx$.",
            "\\arctan x + C",
            topic=TOPIC_INTEGR,
        ),
        math(
            "Вычислите $\\displaystyle \\int \\frac{2x+1}{x^2+x}\\,dx$.",
            "\\ln|x^2+x|+C",
            topic=TOPIC_INTEGR,
        ),
    ])
    return cards


def _limits() -> list[dict]:
    cards: list[dict] = []
    classic = [
        ("\\frac{\\sin x}{x}", "0", "1"),
        ("\\frac{\\tan x}{x}", "0", "1"),
        ("\\frac{1-\\cos x}{x^2}", "0", "\\frac{1}{2}"),
        ("\\frac{e^x-1}{x}", "0", "1"),
        ("\\frac{\\ln(1+x)}{x}", "0", "1"),
        ("\\frac{a^x-1}{x}", "0", "\\ln a"),
        ("\\frac{\\sin 3x}{x}", "0", "3"),
        ("\\frac{\\sin 5x}{\\sin 2x}", "0", "\\frac{5}{2}"),
    ]
    for f, a, val in classic:
        cards.append(
            math(f"Найдите $\\displaystyle \\lim_{{x \\to {a}}} {f}$.", f"\\lim_{{x \\to {a}}} {f} = {val}", topic=TOPIC_LIMITS)
        )

    rational = [
        ("\\frac{x^2-1}{x-1}", "1", "2"),
        ("\\frac{x^2-4}{x-2}", "2", "4"),
        ("\\frac{x^3-8}{x-2}", "2", "12"),
        ("\\frac{x^2+x-6}{x-2}", "2", "5"),
        ("\\frac{\\sqrt{x}-1}{x-1}", "1", "\\frac{1}{2}"),
        ("\\frac{\\sqrt{x+3}-2}{x-1}", "1", "\\frac{1}{4}"),
    ]
    for f, a, val in rational:
        cards.append(
            math(f"Вычислите $\\displaystyle \\lim_{{x \\to {a}}} {f}$.", f"\\lim_{{x \\to {a}}} {f} = {val}", topic=TOPIC_LIMITS)
        )

    infinity = [
        ("\\frac{3x^2+1}{2x^2-x}", "+\\infty", "\\frac{3}{2}"),
        ("\\frac{5x+1}{x^2+2}", "+\\infty", "0"),
        ("\\frac{x^2+1}{3x+2}", "+\\infty", "+\\infty"),
        ("\\left(1+\\frac{1}{x}\\right)^x", "+\\infty", "e"),
        ("\\left(1+\\frac{2}{x}\\right)^{3x}", "+\\infty", "e^6"),
        ("\\frac{\\ln x}{x}", "+\\infty", "0"),
        ("\\frac{x}{e^x}", "+\\infty", "0"),
    ]
    for f, a, val in infinity:
        cards.append(
            math(f"Найдите $\\displaystyle \\lim_{{x \\to {a}}} {f}$.", f"\\lim_{{x \\to {a}}} {f} = {val}", topic=TOPIC_LIMITS)
        )

    one_sided = [
        ("\\frac{|x|}{x}", "0^+", "1"),
        ("\\frac{|x|}{x}", "0^-", "-1"),
        ("\\frac{1}{x}", "0^+", "+\\infty"),
        ("\\frac{1}{x}", "0^-", "-\\infty"),
        ("\\lfloor x \\rfloor", "2^-", "1"),
        ("\\lfloor x \\rfloor", "2^+", "2"),
    ]
    for f, a, val in one_sided:
        cards.append(
            math(f"Найдите $\\displaystyle \\lim_{{x \\to {a}}} {f}$.", f"\\lim_{{x \\to {a}}} {f} = {val}", topic=TOPIC_LIMITS)
        )

    cards.extend([
        math(
            "Проверьте непрерывность $f(x)=\\frac{\\sin x}{x}$ в $x=0$, если $f(0)=1$.",
            "\\lim_{x\\to0} f(x)=1=f(0) \\Rightarrow f\\ непрерывна\\ в\\ 0",
            topic=TOPIC_LIMITS,
        ),
        math(
            "Найдите $\\displaystyle \\lim_{x\\to0}\\frac{\\sqrt{1+x}-\\sqrt{1-x}}{x}$.",
            "\\lim_{x\\to0}\\frac{\\sqrt{1+x}-\\sqrt{1-x}}{x}=1",
            topic=TOPIC_LIMITS,
        ),
        math(
            "Найдите $\\displaystyle \\lim_{x\\to\\infty}\\frac{\\sin x}{x}$.",
            "\\left|\\frac{\\sin x}{x}\\right|\\le\\frac{1}{|x|}\\to0",
            topic=TOPIC_LIMITS,
        ),
        math(
            "Найдите $\\displaystyle \\lim_{x\\to0}(1+3x)^{1/x}$.",
            "e^3",
            topic=TOPIC_LIMITS,
        ),
        math(
            "Найдите $\\displaystyle \\lim_{x\\to0}\\frac{e^{2x}-1}{\\sin x}$.",
            "2",
            topic=TOPIC_LIMITS,
        ),
        math(
            "Найдите $\\displaystyle \\lim_{x\\to1}\\frac{x^3-1}{x-1}$.",
            "3",
            topic=TOPIC_LIMITS,
        ),
        math(
            "Найдите $\\displaystyle \\lim_{n\\to\\infty}\\frac{2n+1}{n+3}$.",
            "2",
            topic=TOPIC_LIMITS,
        ),
        math(
            "Найдите $\\displaystyle \\lim_{n\\to\\infty}\\left(\\frac{n+1}{n}\\right)^n$.",
            "e",
            topic=TOPIC_LIMITS,
        ),
    ])
    return cards


def _series() -> list[dict]:
    cards: list[dict] = []
    maclaurin = [
        ("e^x", "1 + x + \\frac{x^2}{2!} + \\frac{x^3}{3!} + o(x^3)"),
        ("\\sin x", "x - \\frac{x^3}{3!} + o(x^3)"),
        ("\\cos x", "1 - \\frac{x^2}{2!} + \\frac{x^4}{4!} + o(x^4)"),
        ("\\ln(1+x)", "x - \\frac{x^2}{2} + \\frac{x^3}{3} + o(x^3)"),
        ("\\frac{1}{1-x}", "1 + x + x^2 + x^3 + o(x^3)"),
        ("\\arctan x", "x - \\frac{x^3}{3} + o(x^3)"),
        ("(1+x)^\\alpha", "1 + \\alpha x + \\frac{\\alpha(\\alpha-1)}{2}x^2 + o(x^2)"),
    ]
    for f, series in maclaurin:
        cards.append(
            math(
                f"Разложите ${f}$ в ряд Маклорена до $x^3$ включительно (или до указанного порядка).",
                f"{f} = {series}",
                topic=TOPIC_SERIES,
            )
        )

    taylor = [
        ("\\sin x", "0", "x + o(x)"),
        ("e^x", "1", "e + e(x-1) + \\frac{e}{2}(x-1)^2 + o((x-1)^2)"),
        ("\\ln x", "1", "\\ln 1 + (x-1) - \\frac{(x-1)^2}{2} + o((x-1)^2)"),
        ("\\sqrt{x}", "1", "1 + \\frac{x-1}{2} - \\frac{(x-1)^2}{8} + o((x-1)^2)"),
    ]
    for f, x0, series in taylor:
        cards.append(
            math(
                f"Запишите формулу Тейлора для ${f}$ в окрестности $x_0={x0}$ до 2-го порядка.",
                f"{f} = {series}",
                topic=TOPIC_SERIES,
            )
        )

    cards.extend([
        math(
            "Запишите общую формулу Тейлора для $f(x)$ в окрестности $x_0$ до $n$-го порядка.",
            "f(x)=\\sum_{k=0}^{n}\\frac{f^{(k)}(x_0)}{k!}(x-x_0)^k + o((x-x_0)^n)",
            topic=TOPIC_SERIES,
        ),
        math(
            "Найдите сумму геометрического ряда $\\sum_{n=0}^{\\infty} q^n$ при $|q|<1$.",
            "\\sum_{n=0}^{\\infty} q^n = \\frac{1}{1-q}",
            topic=TOPIC_SERIES,
        ),
        math(
            "Найдите сумму $\\sum_{n=1}^{\\infty}\\frac{1}{2^n}$.",
            "1",
            topic=TOPIC_SERIES,
        ),
        math(
            "Найдите сумму $\\sum_{n=0}^{\\infty}\\frac{1}{3^n}$.",
            "\\frac{3}{2}",
            topic=TOPIC_SERIES,
        ),
        math(
            "Найдите $S_N=\\sum_{n=1}^{N} n$.",
            "S_N=\\frac{N(N+1)}{2}",
            topic=TOPIC_SERIES,
        ),
        math(
            "Найдите $S_N=\\sum_{n=1}^{N} n^2$.",
            "S_N=\\frac{N(N+1)(2N+1)}{6}",
            topic=TOPIC_SERIES,
        ),
        math(
            "Признак Даламбера: когда ряд $\\sum a_n$ сходится?",
            "если\\ \\lim\\frac{a_{n+1}}{a_n}<1",
            topic=TOPIC_SERIES,
        ),
        math(
            "Признак Коши: когда ряд $\\sum a_n$ расходится?",
            "если\\ \\lim\\sqrt[n]{|a_n|}>1",
            topic=TOPIC_SERIES,
        ),
        math(
            "Оцените $e^{0.1}$ по разложению $e^x$ до $x^2$.",
            "e^{0.1}\\approx1+0.1+\\frac{0.01}{2}=1.105",
            topic=TOPIC_SERIES,
        ),
        math(
            "Оцените $\\sin(0.1)$ по разложению до $x^3$.",
            "\\sin(0.1)\\approx0.1-\\frac{0.001}{6}\\approx0.09983",
            topic=TOPIC_SERIES,
        ),
        math(
            "Найдите радиус сходимости $\\sum_{n=0}^{\\infty}\\frac{x^n}{n!}$.",
            "R=+\\infty",
            topic=TOPIC_SERIES,
        ),
        math(
            "Найдите радиус сходимости $\\sum_{n=0}^{\\infty} x^n$.",
            "R=1",
            topic=TOPIC_SERIES,
        ),
        math(
            "Разложите $\\cos x$ до $x^4$ и найдите коэффициент при $x^2$.",
            "1 - \\frac{x^2}{2} + \\frac{x^4}{24} + o(x^4);\\ коэффициент\\ -\\frac{1}{2}",
            topic=TOPIC_SERIES,
        ),
        math(
            "Разложите $e^{-x}$ в ряд Маклорена до $x^3$.",
            "1 - x + \\frac{x^2}{2} - \\frac{x^3}{6} + o(x^3)",
            topic=TOPIC_SERIES,
        ),
        math(
            "Разложите $\\sin(2x)$ до $x^3$.",
            "2x - \\frac{8x^3}{6} + o(x^3)",
            topic=TOPIC_SERIES,
        ),
        math(
            "Разложите $\\ln(1-x)$ до $x^3$.",
            "-x - \\frac{x^2}{2} - \\frac{x^3}{3} + o(x^3)",
            topic=TOPIC_SERIES,
        ),
        math(
            "Найдите остаток в форме Лагранжа для Тейлора 1-го порядка $f(x)$ в $x_0$.",
            "R_1(x)=\\frac{f''(\\xi)}{2}(x-x_0)^2,\\ \\xi\\ между\\ x\\ и\\ x_0",
            topic=TOPIC_SERIES,
        ),
        math(
            "Частичная сумма $S_3$ для $\\sum_{n=0}^{\\infty} x^n$.",
            "S_3=1+x+x^2+x^3",
            topic=TOPIC_SERIES,
        ),
        math(
            "Найдите сумму $\\sum_{n=1}^{\\infty}\\frac{1}{n(n+1)}$ (телескоп).",
            "1",
            topic=TOPIC_SERIES,
        ),
    ])
    return cards


def _matrices() -> list[dict]:
    cards: list[dict] = []
    det2 = [
        ("\\begin{pmatrix} 2 & 1 \\\\ 5 & 3 \\end{pmatrix}", "1"),
        ("\\begin{pmatrix} 1 & 2 \\\\ 3 & 4 \\end{pmatrix}", "-2"),
        ("\\begin{pmatrix} 3 & 2 \\\\ 1 & 4 \\end{pmatrix}", "10"),
        ("\\begin{pmatrix} 0 & 1 \\\\ 1 & 0 \\end{pmatrix}", "-1"),
        ("\\begin{pmatrix} 2 & 0 \\\\ 0 & 3 \\end{pmatrix}", "6"),
        ("\\begin{pmatrix} -1 & 2 \\\\ 3 & -4 \\end{pmatrix}", "-2"),
    ]
    for A, val in det2:
        cards.append(math(f"Вычислите $\\det A$, где $A={A}$.", f"\\det A = {val}", topic=TOPIC_MATRICES))

    mult = [
        (
            "\\begin{pmatrix} 1 & 2 \\\\ 0 & 1 \\end{pmatrix}",
            "\\begin{pmatrix} 3 & 1 \\\\ 2 & 4 \\end{pmatrix}",
            "\\begin{pmatrix} 7 & 9 \\\\ 2 & 4 \\end{pmatrix}",
        ),
        (
            "\\begin{pmatrix} 1 & 0 \\\\ 2 & 1 \\end{pmatrix}",
            "\\begin{pmatrix} 1 & 2 \\\\ 3 & 4 \\end{pmatrix}",
            "\\begin{pmatrix} 1 & 2 \\\\ 5 & 8 \\end{pmatrix}",
        ),
        (
            "\\begin{pmatrix} 2 & 1 \\\\ 1 & 1 \\end{pmatrix}",
            "\\begin{pmatrix} 1 & 3 \\\\ 2 & 1 \\end{pmatrix}",
            "\\begin{pmatrix} 4 & 7 \\\\ 3 & 4 \\end{pmatrix}",
        ),
    ]
    for A, B, AB in mult:
        cards.append(math(f"Найдите $AB$, если $A={A}$, $B={B}$.", f"AB = {AB}", topic=TOPIC_MATRICES))

    inv = [
        ("\\begin{pmatrix} 1 & 2 \\\\ 3 & 4 \\end{pmatrix}", "\\begin{pmatrix} -2 & 1 \\\\ 1.5 & -0.5 \\end{pmatrix}"),
        ("\\begin{pmatrix} 2 & 1 \\\\ 5 & 3 \\end{pmatrix}", "\\begin{pmatrix} 3 & -1 \\\\ -5 & 2 \\end{pmatrix}"),
        ("\\begin{pmatrix} 1 & 1 \\\\ 0 & 1 \\end{pmatrix}", "\\begin{pmatrix} 1 & -1 \\\\ 0 & 1 \\end{pmatrix}"),
    ]
    for A, Ainv in inv:
        cards.append(math(f"Найдите $A^{{-1}}$ для $A={A}$.", f"A^{{-1}} = {Ainv}", topic=TOPIC_MATRICES))

    cards.extend([
        math(
            "Вычислите $\\det\\begin{pmatrix} 1 & 0 & 2 \\\\ 0 & 3 & 1 \\\\ 4 & 0 & 5 \\end{pmatrix}$.",
            "\\det = -9",
            topic=TOPIC_MATRICES,
        ),
        math(
            "Вычислите $\\det\\begin{pmatrix} 1 & 2 & 3 \\\\ 0 & 1 & 4 \\\\ 0 & 0 & 5 \\end{pmatrix}$.",
            "\\det = 5",
            topic=TOPIC_MATRICES,
        ),
        math(
            "Найдите $(A^T)^T$ для любой матрицы $A$.",
            "(A^T)^T = A",
            topic=TOPIC_MATRICES,
        ),
        math(
            "Найдите $(AB)^T$, если $A,B$ — матрицы $m\\times n$ и $n\\times p$.",
            "(AB)^T = B^T A^T",
            topic=TOPIC_MATRICES,
        ),
        math(
            "Вычислите $\\det\\begin{pmatrix} 2 & 0 & 0 \\\\ 0 & 3 & 0 \\\\ 0 & 0 & 4 \\end{pmatrix}$.",
            "\\det = 24",
            topic=TOPIC_MATRICES,
        ),
        math(
            "Найдите след $\\operatorname{tr}(A)$ для $A=\\begin{pmatrix} 1 & 2 \\\\ 3 & 4 \\end{pmatrix}$.",
            "\\operatorname{tr}(A)=5",
            topic=TOPIC_MATRICES,
        ),
        math(
            "Является ли $A=\\begin{pmatrix} 1 & 2 \\\\ 2 & 4 \\end{pmatrix}$ обратимой?",
            "\\det A=0 \\Rightarrow A\\ необратима",
            topic=TOPIC_MATRICES,
        ),
        math(
            "Найдите $2A$ для $A=\\begin{pmatrix} 1 & -1 \\\\ 2 & 0 \\end{pmatrix}$.",
            "2A=\\begin{pmatrix} 2 & -2 \\\\ 4 & 0 \\end{pmatrix}",
            topic=TOPIC_MATRICES,
        ),
        math(
            "Найдите $A-B$ для $A=\\begin{pmatrix} 3 & 1 \\\\ 2 & 4 \\end{pmatrix}$, $B=\\begin{pmatrix} 1 & 0 \\\\ 1 & 2 \\end{pmatrix}$.",
            "A-B=\\begin{pmatrix} 2 & 1 \\\\ 1 & 2 \\end{pmatrix}",
            topic=TOPIC_MATRICES,
        ),
        math(
            "Найдите $\\det(kA)$, если $A$ — $n\\times n$, $\\det A=5$.",
            "\\det(kA)=k^n\\det A = 5k^n",
            topic=TOPIC_MATRICES,
        ),
        math(
            "Вычислите $\\det\\begin{pmatrix} 1 & 1 & 1 \\\\ 1 & 2 & 3 \\\\ 1 & 4 & 9 \\end{pmatrix}$.",
            "\\det = 2",
            topic=TOPIC_MATRICES,
        ),
        math(
            "Найдите ранг $\\begin{pmatrix} 1 & 0 \\\\ 2 & 0 \\end{pmatrix}$.",
            "\\operatorname{rank}=1",
            topic=TOPIC_MATRICES,
        ),
        math(
            "Найдите $A^2$ для $A=\\begin{pmatrix} 0 & 1 \\\\ 0 & 0 \\end{pmatrix}$.",
            "A^2=\\begin{pmatrix} 0 & 0 \\\\ 0 & 0 \\end{pmatrix}",
            topic=TOPIC_MATRICES,
        ),
        math(
            "Найдите единичную матрицу $I_3$.",
            "I_3=\\begin{pmatrix}1&0&0\\\\0&1&0\\\\0&0&1\\end{pmatrix}",
            topic=TOPIC_MATRICES,
        ),
        math(
            "Найдите $\\det\\begin{pmatrix} a & b \\\\ c & d \\end{pmatrix}$.",
            "ad-bc",
            topic=TOPIC_MATRICES,
        ),
        math(
            "Найдите обратную для $\\begin{pmatrix} 3 & 0 \\\\ 0 & 5 \\end{pmatrix}$.",
            "A^{-1}=\\begin{pmatrix} 1/3 & 0 \\\\ 0 & 1/5 \\end{pmatrix}",
            topic=TOPIC_MATRICES,
        ),
        math(
            "Вычислите $\\det\\begin{pmatrix} 1 & 2 & 0 \\\\ 3 & 1 & 1 \\\\ 0 & 1 & 2 \\end{pmatrix}$.",
            "\\det = -9",
            topic=TOPIC_MATRICES,
        ),
        math(
            "Найдите $A^T$ для $A=\\begin{pmatrix} 1 & 2 & 3 \\end{pmatrix}$ (строка).",
            "A^T=\\begin{pmatrix}1\\\\2\\\\3\\end{pmatrix}",
            topic=TOPIC_MATRICES,
        ),
    ])
    return cards


def _linear_algebra() -> list[dict]:
    cards: list[dict] = []
    systems = [
        ("\\begin{cases} x+y=5 \\\\ 2x-y=1 \\end{cases}", "x=2,\\ y=3"),
        ("\\begin{cases} 2x+y=7 \\\\ x-y=2 \\end{cases}", "x=3,\\ y=1"),
        ("\\begin{cases} x+2y=8 \\\\ 3x-y=1 \\end{cases}", "x=2,\\ y=3"),
        ("\\begin{cases} x-y=0 \\\\ 2x+y=9 \\end{cases}", "x=3,\\ y=3"),
        ("\\begin{cases} 3x+2y=12 \\\\ x-y=1 \\end{cases}", "x=2,\\ y=3"),
    ]
    for sys, sol in systems:
        cards.append(math(f"Решите систему ${sys}$.", sol, topic=TOPIC_LINEAR))

    eigen = [
        ("\\begin{pmatrix} 4 & 1 \\\\ 2 & 3 \\end{pmatrix}", "\\lambda_1=5,\\ \\lambda_2=2"),
        ("\\begin{pmatrix} 2 & 0 \\\\ 0 & 3 \\end{pmatrix}", "\\lambda_1=2,\\ \\lambda_2=3"),
        ("\\begin{pmatrix} 0 & 1 \\\\ -2 & 3 \\end{pmatrix}", "\\lambda_1=1,\\ \\lambda_2=2"),
        ("\\begin{pmatrix} 1 & 2 \\\\ 2 & 1 \\end{pmatrix}", "\\lambda_1=3,\\ \\lambda_2=-1"),
        ("\\begin{pmatrix} 5 & -1 \\\\ 2 & 2 \\end{pmatrix}", "\\lambda_1=4,\\ \\lambda_2=3"),
    ]
    for A, vals in eigen:
        cards.append(
            math(f"Найдите собственные значения $A={A}$.", vals, topic=TOPIC_LINEAR)
        )

    cards.extend([
        math(
            "Вычислите ранг $A=\\begin{pmatrix} 1 & 2 & 3 \\\\ 2 & 4 & 6 \\\\ 1 & 1 & 1 \\end{pmatrix}$.",
            "\\operatorname{rank} A = 2",
            topic=TOPIC_LINEAR,
        ),
        math(
            "Вычислите ранг $A=\\begin{pmatrix} 1 & 0 \\\\ 0 & 1 \\\\ 1 & 1 \\end{pmatrix}$.",
            "\\operatorname{rank} A = 2",
            topic=TOPIC_LINEAR,
        ),
        math(
            "Найдите собственный вектор для $\\lambda=5$ матрицы $\\begin{pmatrix}4&1\\\\2&3\\end{pmatrix}$.",
            "v=(1,1)^T",
            topic=TOPIC_LINEAR,
        ),
        math(
            "Найдите характеристическое уравнение $A=\\begin{pmatrix}a&b\\\\c&d\\end{pmatrix}$.",
            "\\lambda^2-(a+d)\\lambda+(ad-bc)=0",
            topic=TOPIC_LINEAR,
        ),
        math(
            "Решите $\\begin{pmatrix}1&2\\\\3&4\\end{pmatrix}x=\\begin{pmatrix}5\\\\11\\end{pmatrix}$.",
            "x=\\begin{pmatrix}1\\\\2\\end{pmatrix}",
            topic=TOPIC_LINEAR,
        ),
        math(
            "Сколько решений у системы 3 уравнений с 2 неизвестными при rank=2?",
            "либо\\ нет,\\ либо\\ бесконечно\\ много\\ (если\\ совместна)",
            topic=TOPIC_LINEAR,
        ),
        math(
            "Найдите $\\det A$ для $A=\\begin{pmatrix}2&1&0\\\\0&2&1\\\\0&0&2\\end{pmatrix}$ (верхняя треугольная).",
            "\\det A=8",
            topic=TOPIC_LINEAR,
        ),
        math(
            "Являются ли векторы $(1,0)$ и $(2,0)$ линейно зависимыми?",
            "да,\\ v_2=2v_1",
            topic=TOPIC_LINEAR,
        ),
        math(
            "Найдите размерность подпространства, натянутого на $(1,0,0)$ и $(0,1,0)$ в $\\mathbb{R}^3$.",
            "2",
            topic=TOPIC_LINEAR,
        ),
        math(
            "Решите методом Крамера 2×2: $\\begin{cases}2x+y=5\\\\x-y=1\\end{cases}$.",
            "x=2,\\ y=1",
            topic=TOPIC_LINEAR,
        ),
        math(
            "Найдите $\\operatorname{null}(A)$ для $A=\\begin{pmatrix}1&2&3\\\\2&4&6\\end{pmatrix}$ (размерность).",
            "\\dim\\ker A=1",
            topic=TOPIC_LINEAR,
        ),
        math(
            "Ортонормируйте $(1,1)$ и $(1,0)$ (Gram–Schmidt в $\\mathbb{R}^2$).",
            "e_1=\\frac{1}{\\sqrt2}(1,1),\\ e_2=\\frac{1}{\\sqrt2}(1,-1)",
            topic=TOPIC_LINEAR,
        ),
        math(
            "Найдите $\\|x\\|$ для $x=(3,4)$ в $\\mathbb{R}^2$.",
            "\\|x\\|=5",
            topic=TOPIC_LINEAR,
        ),
        math(
            "Найдите проекцию $(4,0)$ на $(1,1)$.",
            "(2,2)",
            topic=TOPIC_LINEAR,
        ),
        math(
            "Диагонализируема ли $\\begin{pmatrix}2&1\\\\0&2\\end{pmatrix}$?",
            "нет\\ (жordan\\ cell,\\ не\\ два\\ собственных\\ вектора)",
            topic=TOPIC_LINEAR,
        ),
        math(
            "Найдите след матрицы с собственными значениями $2,3,5$.",
            "\\operatorname{tr}=10",
            topic=TOPIC_LINEAR,
        ),
        math(
            "Найдите $\\det A$, если собственные значения $1,2,3$.",
            "\\det A=6",
            topic=TOPIC_LINEAR,
        ),
        math(
            "Решите однородную систему $\\begin{cases}x+y+z=0\\\\2x+2y+2z=0\\end{cases}$ (опишите решение).",
            "x=-s-t,\\ y=s,\\ z=t",
            topic=TOPIC_LINEAR,
        ),
        math(
            "Найдите ранг диагональной $3\\times3$ с двумя ненулевыми диагональными элементами.",
            "2",
            topic=TOPIC_LINEAR,
        ),
        math(
            "Найдите $Av$ для $A=I_2$, $v=(3,-1)^T$.",
            "Av=v",
            topic=TOPIC_LINEAR,
        ),
        math(
            "Существует ли ненулевой $x$: $Ax=0$ при $\\det A\\ne0$?",
            "нет,\\ только\\ x=0",
            topic=TOPIC_LINEAR,
        ),
        math(
            "Найдите базис $\\ker\\begin{pmatrix}1&-1\\end{pmatrix}$.",
            "(1,1)^T",
            topic=TOPIC_LINEAR,
        ),
        math(
            "Найдите координаты $(2,1)$ в базисе $e_1=(1,0)$, $e_2=(0,1)$.",
            "(2,1)",
            topic=TOPIC_LINEAR,
        ),
        math(
            "Найдите $\\lambda$ для которых $\\det\\begin{pmatrix}\\lambda&1\\\\1&\\lambda\\end{pmatrix}=0$.",
            "\\lambda=\\pm1",
            topic=TOPIC_LINEAR,
        ),
        math(
            "Решите $\\begin{cases}x+2y+z=4\\\\2x+5y+z=9\\end{cases}$ (одна свободная).",
            "z=t,\\ x=2-t,\\ y=1",
            topic=TOPIC_LINEAR,
        ),
    ])
    return cards


def _vectors() -> list[dict]:
    cards: list[dict] = []
    dot = [
        ((1, 2, -1), (2, 0, 3), "-1"),
        ((1, 1), (1, 0), "1"),
        ((3, 4), (4, 3), "24"),
        ((1, 2, 3), (0, 0, 1), "3"),
        ((2, -1, 2), (1, 0, -2), "0"),
    ]
    for a, b, val in dot:
        cards.append(
            math(
                f"Вычислите $\\vec{{a}}\\cdot\\vec{{b}}$, если $\\vec{{a}}={a}$, $\\vec{{b}}={b}$.",
                f"\\vec{{a}}\\cdot\\vec{{b}}={val}",
                topic=TOPIC_VECTORS,
            )
        )

    cross = [
        ((1, 0, 0), (0, 1, 0), "(0,0,1)"),
        ((1, 0, 0), (0, 0, 1), "(0,-1,0)"),
        ((2, 0, 0), (0, 3, 0), "(0,0,6)"),
        ((1, 1, 0), (0, 1, 1), "(1,-1,1)"),
    ]
    for a, b, val in cross:
        cards.append(
            math(
                f"Найдите $\\vec{{a}}\\times\\vec{{b}}$, $\\vec{{a}}={a}$, $\\vec{{b}}={b}$.",
                f"\\vec{{a}}\\times\\vec{{b}}={val}",
                topic=TOPIC_VECTORS,
            )
        )

    length = [
        ((3, 4), "5"),
        ((1, 2, 2), "3"),
        ((6, 8, 0), "10"),
        ((1, 1, 1), "\\sqrt{3}"),
    ]
    for v, val in length:
        cards.append(
            math(f"Найдите длину $\\vec{{v}}={v}$.", f"|\\vec{{v}}|={val}", topic=TOPIC_VECTORS)
        )

    cards.extend([
        math(
            "Найдите угол между $(1,0)$ и $(1,1)$ в градусах.",
            "\\cos\\theta=\\frac{1}{\\sqrt2}\\Rightarrow\\theta=45^\\circ",
            topic=TOPIC_VECTORS,
        ),
        math(
            "Найдите проекцию $\\vec{a}=(4,0)$ на $\\vec{b}=(1,1)$.",
            "\\operatorname{proj}_{\\vec b}\\vec a=(2,2)",
            topic=TOPIC_VECTORS,
        ),
        math(
            "Комplanarны ли $(1,0,0)$, $(0,1,0)$, $(1,1,0)$?",
            "да,\\ третий\\ —\\ сумма\\ первых\\ двух",
            topic=TOPIC_VECTORS,
        ),
        math(
            "Найдите единичный вектор направления $(3,4)$.",
            "\\left(\\frac{3}{5},\\frac{4}{5}\\right)",
            topic=TOPIC_VECTORS,
        ),
        math(
            "Найдите $\\vec{a}\\cdot\\vec{b}$, если $|\\vec a|=3$, $|\\vec b|=4$, угол $60^\\circ$.",
            "6",
            topic=TOPIC_VECTORS,
        ),
        math(
            "Найдите площадь параллелограмма на $(2,0,0)$ и $(0,3,0)$.",
            "6",
            topic=TOPIC_VECTORS,
        ),
        math(
            "Найдите объём параллелепипеда на $(1,0,0)$, $(0,2,0)$, $(0,0,3)$.",
            "6",
            topic=TOPIC_VECTORS,
        ),
        math(
            "Ортогональны ли $(1,2)$ и $(2,-1)$?",
            "да,\\ (1,2)\\cdot(2,-1)=0",
            topic=TOPIC_VECTORS,
        ),
        math(
            "Найдите расстояние между точками $(1,2)$ и $(4,6)$.",
            "5",
            topic=TOPIC_VECTORS,
        ),
        math(
            "Найдите $\\vec r(t)=(\\cos t,\\sin t)$ — что это за кривая?",
            "окружность\\ радиуса\\ 1",
            topic=TOPIC_VECTORS,
        ),
        math(
            "Найдите $\\frac{d}{dt}(\\vec r)$ для $\\vec r(t)=(t,t^2)$.",
            "\\vec r'(t)=(1,2t)",
            topic=TOPIC_VECTORS,
        ),
        math(
            "Найдите $|\\vec r'(1)|$ для $\\vec r(t)=(t,t^2)$.",
            "\\sqrt{5}",
            topic=TOPIC_VECTORS,
        ),
        math(
            "Найдите смешанное произведение $(1,0,0)\\cdot((0,1,0)\\times(0,0,1))$.",
            "1",
            topic=TOPIC_VECTORS,
        ),
        math(
            "Найдите $\\vec n$ — нормаль к плоскости $2x-y+z=1$.",
            "\\vec n=(2,-1,1)",
            topic=TOPIC_VECTORS,
        ),
        math(
            "Найдите расстояние от $(0,0,0)$ до плоскости $x+y+z=3$.",
            "\\sqrt{3}",
            topic=TOPIC_VECTORS,
        ),
        math(
            "Найдите параметрическое уравнение прямой через $(0,0)$ и $(1,2)$.",
            "(x,y)=(t,2t)",
            topic=TOPIC_VECTORS,
        ),
        math(
            "Найдите $\\vec a\\times\\vec a$ для любого $\\vec a$.",
            "\\vec 0",
            topic=TOPIC_VECTORS,
        ),
        math(
            "Найдите $\\vec a\\cdot(\\vec b\\times\\vec c)$ — что означает знак?",
            "ориентированный\\ объём\\ параллелепипеда",
            topic=TOPIC_VECTORS,
        ),
        math(
            "Декартова форма $(2,3)$ + $(-1,1)$.",
            "(1,4)",
            topic=TOPIC_VECTORS,
        ),
        math(
            "Найдите $\\lambda$, чтобы $(1,2)$ и $(2,\\lambda)$ ортогональны.",
            "\\lambda=-1",
            topic=TOPIC_VECTORS,
        ),
        math(
            "Найдите угол между $(1,0,0)$ и $(0,1,0)$.",
            "90^\\circ",
            topic=TOPIC_VECTORS,
        ),
    ])
    return cards


def _multivar() -> list[dict]:
    cards: list[dict] = []
    partial = [
        ("x^2 y + \\sin y", "2xy", "x^2 + \\cos y"),
        ("x^2 + y^2", "2x", "2y"),
        ("e^{xy}", "y e^{xy}", "x e^{xy}"),
        ("\\ln(x^2+y^2)", "\\frac{2x}{x^2+y^2}", "\\frac{2y}{x^2+y^2}"),
        ("x^3 y^2", "3x^2 y^2", "2x^3 y"),
        ("\\sin(xy)", "y\\cos(xy)", "x\\cos(xy)"),
    ]
    for f, fx, fy in partial:
        cards.append(
            math(
                f"Найдите $\\frac{{\\partial f}}{{\\partial x}}$, $\\frac{{\\partial f}}{{\\partial y}}$ для $f(x,y)={f}$.",
                f"\\frac{{\\partial f}}{{\\partial x}}={fx},\\quad \\frac{{\\partial f}}{{\\partial y}}={fy}",
                topic=TOPIC_MULTIVAR,
            )
        )

    cards.extend([
        math(
            "Вычислите градиент $\\nabla f$ в $(1,2)$ для $f(x,y)=x^2+y^2$.",
            "\\nabla f=(2x,2y),\\ \\nabla f(1,2)=(2,4)",
            topic=TOPIC_MULTIVAR,
        ),
        math(
            "Найдите $\\nabla f$ для $f(x,y,z)=x+y+z$.",
            "\\nabla f=(1,1,1)",
            topic=TOPIC_MULTIVAR,
        ),
        math(
            "Найдите $\\nabla \\cdot \\vec F$ для $\\vec F=(x,y,z)$.",
            "3",
            topic=TOPIC_MULTIVAR,
        ),
        math(
            "Найдите $\\nabla \\cdot \\vec F$ для $\\vec F=(x^2, y, z^2)$.",
            "2x+1+2z",
            topic=TOPIC_MULTIVAR,
        ),
        math(
            "Найдите $\\nabla \\times \\vec F$ для $\\vec F=(0,0,z)$.",
            "(0,0,0)",
            topic=TOPIC_MULTIVAR,
        ),
        math(
            "Найдите $\\nabla \\times \\vec F$ для $\\vec F=(y,-x,0)$.",
            "(0,0,-2)",
            topic=TOPIC_MULTIVAR,
        ),
        math(
            "Найдите уравнение касательной плоскости к $z=x^2+y^2$ в $(1,1,2)$.",
            "z-2=2(x-1)+2(y-1)",
            topic=TOPIC_MULTIVAR,
        ),
        math(
            "Найдите направление наибольшего роста $f(x,y)=xy$ в $(2,3)$.",
            "\\nabla f=(y,x)=(3,2)",
            topic=TOPIC_MULTIVAR,
        ),
        math(
            "Найдите производную по направлению $D_{\\vec u}f$ при $\\vec u=(1,0)$, $f=x^2+y$ в $(1,2)$.",
            "D_{\\vec u}f=2",
            topic=TOPIC_MULTIVAR,
        ),
        math(
            "Найдите стационарные точки $f(x,y)=x^2+y^2-2x$.",
            "(1,0)",
            topic=TOPIC_MULTIVAR,
        ),
        math(
            "Классифицируйте стационарную точку $f(x,y)=x^2+y^2$ в $(0,0)$.",
            "минимум\\ (H=\\begin{pmatrix}2&0\\\\0&2\\end{pmatrix}\\ positive)",
            topic=TOPIC_MULTIVAR,
        ),
        math(
            "Найдите $\\frac{\\partial^2 f}{\\partial x\\partial y}$ для $f=xy^2$.",
            "2y",
            topic=TOPIC_MULTIVAR,
        ),
        math(
            "Проверьте равенство $\\frac{\\partial^2 f}{\\partial x\\partial y}=\\frac{\\partial^2 f}{\\partial y\\partial x}$ для $f=e^{xy}$.",
            "e^{xy}(1+xy)",
            topic=TOPIC_MULTIVAR,
        ),
        math(
            "Вычислите $\\iint_D 1\\,dxdy$, $D=[0,1]\\times[0,2]$.",
            "2",
            topic=TOPIC_MULTIVAR,
        ),
        math(
            "Вычислите $\\iint_D xy\\,dxdy$, $D=[0,1]\\times[0,1]$.",
            "\\frac{1}{4}",
            topic=TOPIC_MULTIVAR,
        ),
        math(
            "Перейдите в полярные: $x=r\\cos\\theta$, $y=r\\sin\\theta$, $dxdy=?$.",
            "dxdy=r\\,dr\\,d\\theta",
            topic=TOPIC_MULTIVAR,
        ),
        math(
            "Найдите $\\frac{dz}{dt}$ при $z=x^2+y^2$, $x=t$, $y=t^2$.",
            "2t+4t^3",
            topic=TOPIC_MULTIVAR,
        ),
        math(
            "Найдите $\\frac{\\partial z}{\\partial x}$ для $z=f(x,y)$, $y=g(x)$ (цепное правило).",
            "f_x + f_y g'(x)",
            topic=TOPIC_MULTIVAR,
        ),
        math(
            "Найдите $\\lim_{(x,y)\\to(0,0)}\\frac{xy}{x^2+y^2}$.",
            "не\\ существует\\ (разные\\ пути)",
            topic=TOPIC_MULTIVAR,
        ),
        math(
            "Найдите $\\nabla f$ для $f=\\arctan(y/x)$.",
            "\\left(\\frac{-y}{x^2+y^2},\\frac{x}{x^2+y^2}\\right)",
            topic=TOPIC_MULTIVAR,
        ),
        math(
            "Является ли $\\vec F=(y,x)$ консervative?",
            "нет,\\ \\frac{\\partial P}{\\partial y}=1\\ne\\frac{\\partial Q}{\\partial x}=1?\\ Q=x,\\ P=y\\ —\\ да\\ conservative",
            topic=TOPIC_MULTIVAR,
        ),
        math(
            "Найдите $\\nabla\\cdot(\\nabla\\times\\vec F)$.",
            "0",
            topic=TOPIC_MULTIVAR,
        ),
        math(
            "Найдите $\\nabla\\times(\\nabla f)$.",
            "\\vec 0",
            topic=TOPIC_MULTIVAR,
        ),
        math(
            "Найдите $\\frac{\\partial f}{\\partial x}$ для $f(x,y)=|xy|$ в $(1,1)$ по направлениям.",
            "не\\ дифференцируема\\ в\\ 0;\\ в\\ (1,1)\\ partial\\ exist",
            topic=TOPIC_MULTIVAR,
        ),
        math(
            "Найдите якобиан $\\frac{\\partial(x,y)}{\\partial(u,v)}$ для $x=u+v$, $y=u-v$.",
            "\\det\\begin{pmatrix}1&1\\\\1&-1\\end{pmatrix}=-2",
            topic=TOPIC_MULTIVAR,
        ),
    ])
    return cards


def build_cards() -> list[dict]:
    parts = [
        _derivatives(),
        _integrals(),
        _limits(),
        _series(),
        _matrices(),
        _linear_algebra(),
        _vectors(),
        _multivar(),
    ]
    return [card for block in parts for card in block]
