import os
from pathlib import Path
from shutil import which

from invoke import task
from invoke.util import cd

TOOLS = ["poetry", "pre-commit"]
PORT = os.environ.get("SERVER_PORT", 8000)

ACTIVE_VENV = os.environ.get("VIRTUAL_ENV", None)
VENV_HOME = Path(os.environ.get("WORKON_HOME", "~/.local/share/virtualenvs"))
VENV_PATH = Path(ACTIVE_VENV) if ACTIVE_VENV else (VENV_HOME / "kagi")
VENV = str(VENV_PATH.expanduser())

PRECOMMIT = which("pre-commit") if which("pre-commit") else (VENV / "pre-commit")
POETRY = which("poetry") if which("poetry") else (VENV / "poetry")


@task
def build(c, docs=True):
    """Build documentation"""
    if docs:
        c.run(f"{VENV}/bin/sphinx-build docs docs/_build")


@task(build)
def livedocs(c):
    """Serve docs at http://localhost:$PORT/ (default port is 8000)"""
    from livereload import Server

    server = Server()
    server.watch("docs/conf.py", lambda: build(c))
    server.watch("CONTRIBUTING.rst", lambda: build(c))
    server.watch("docs/*.rst", lambda: build(c))
    server.serve(port=PORT, root="docs/_build")


@task
def serve(c):
    """Serve site at https://localhost:$PORT/ (default port is 8000)"""
    with cd("testproj"):
        c.run(
            f"{VENV}/bin/python manage.py runserver_plus "
            f"--cert-file {VENV}/localhost.crt "
            f"--key-file {VENV}/localhost.key",
            pty=True,
        )


@task
def tests(c):
    """Run the test suite"""
    c.run(
        f"{VENV}/bin/pytest -s --doctest-modules --cov-report term-missing "
        "--cov-fail-under 100 --cov kagi",
        pty=True,
    )


@task
def makemigrations(c):
    with cd("testproj"):
        c.run(f"{VENV}/bin/python manage.py makemigrations")


@task
def migrate(c):
    with cd("testproj"):
        c.run(f"{VENV}/bin/python manage.py migrate")


@task
def black(c, diff=False):
    """Run Black auto-formatter, optionally with --diff"""
    if diff:
        c.run(f"{VENV}/bin/black --diff kagi testproj")
    else:
        c.run(f"{VENV}/bin/black kagi testproj")


@task
def isort(c):
    c.run(f"{VENV}/bin/isort --recursive .isort.cfg kagi/* testproj/*")


@task
def flake8(c):
    c.run(f"{VENV}/bin/flake8 kagi testproj")


@task
def lint(c):
    c.run(f"{VENV}/bin/isort -c --recursive .isort.cfg kagi/* testproj/*")
    c.run(f"{VENV}/bin/black --check kagi testproj")
    flake8(c)


@task
def tools(c):
    """Install tools in the virtual environment if not already on PATH"""
    for tool in TOOLS:
        if not which(tool):
            c.run(f"{VENV}/bin/pip install {tool}")


@task
def precommit(c):
    """Install pre-commit hooks to .git/hooks/pre-commit"""
    c.run(f"{PRECOMMIT} install")


@task
def setup(c):
    c.run(f"{VENV}/bin/pip install -U pip")
    tools(c)
    c.run(f"{POETRY} install")
