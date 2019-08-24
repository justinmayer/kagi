import os
from pathlib import Path
from shutil import which

from invoke import task
from invoke.util import cd

DEMO_PORT = os.environ.get("DEMO_PORT", 8000)
DOCS_PORT = os.environ.get("DOCS_PORT", 8000)

ACTIVE_VENV = os.environ.get("VIRTUAL_ENV", None)
VENV_HOME = Path(os.environ.get("WORKON_HOME", "~/.local/share/virtualenvs"))
VENV_PATH = Path(ACTIVE_VENV) if ACTIVE_VENV else (VENV_HOME / "kagi")
VENV = str(VENV_PATH.expanduser())

TOOLS = ["poetry", "pre-commit"]
POETRY = which("poetry") if which("poetry") else (VENV / Path("bin") / "poetry")
PRECOMMIT = (
    which("pre-commit") if which("pre-commit") else (VENV / Path("bin") / "pre-commit")
)


@task
def docs(c):
    """Build documentation"""
    c.run(f"{VENV}/bin/sphinx-build docs docs/_build")


@task(docs)
def viewdocs(c):
    """Serve docs at http://localhost:$DOCS_PORT/ (default port is 8000)"""
    from livereload import Server

    server = Server()
    server.watch("docs/conf.py", lambda: docs(c))
    server.watch("CONTRIBUTING.rst", lambda: docs(c))
    server.watch("docs/*.rst", lambda: docs(c))
    server.serve(port=DOCS_PORT, root="docs/_build")


@task
def serve(c):
    """Serve demo site at https://localhost:$DEMO_PORT/ (default port is 8000)"""
    with cd("testproj"):
        c.run(f"{VENV}/bin/python manage.py runserver {DEMO_PORT} ", pty=True)


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
    """Create database migrations if needed"""
    with cd("testproj"):
        c.run(f"{VENV}/bin/python manage.py makemigrations")


@task
def migrate(c):
    """Migrate database to current schema"""
    with cd("testproj"):
        c.run(f"{VENV}/bin/python manage.py migrate")


@task
def black(c, check=False, diff=False):
    """Run Black auto-formatter, optionally with --check or --diff"""
    diff_flag, check_flag = "", ""
    if check:
        check_flag = "--check"
    if diff:
        diff_flag = "--diff"
    c.run(f"{VENV}/bin/black {check_flag} {diff_flag} kagi testproj tasks.py")


@task
def isort(c, check=False):
    check_flag = ""
    if check:
        check_flag = "-c"
    c.run(
        f"{VENV}/bin/isort {check_flag} --recursive .isort.cfg kagi/* testproj/* tasks.py"
    )


@task
def flake8(c):
    c.run(f"{VENV}/bin/flake8 kagi testproj tasks.py")


@task
def lint(c):
    isort(c, check=True)
    black(c, check=True)
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
