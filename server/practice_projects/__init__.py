"""Authored projects, starters, milestone checks and reference implementations."""
from textwrap import dedent


def text(value):
    return dedent(value).strip() + "\n"


def project(id, title, track, chapters, description, runtime, files, steps, checks, solution, preview=False):
    return dict(id=id, title=title, track=track, chapters=chapters, description=description,
                runtime=runtime, files=files, steps=[dict(title=t, task=q) for t, q in steps],
                checks=text(checks), solution=solution, preview=preview,
                entrypoint="main.php" if track == "php" else "main.py")


def catalog():
    from server.practice_projects.python import PROJECTS as python
    from server.practice_projects.php import PROJECTS as php
    return {p["id"]: p for p in [*python, *php]}


def public_project(project):
    return {key: value for key, value in project.items() if key not in {"checks", "solution", "files"}}
