import os
from pathlib import Path
from shutil import which

from invoke import task
from invoke.util import cd

DEMO_PORT = os.environ.get("DEMO_PORT", 8000)
DOCS_PORT = os.environ.get("DOCS_PORT", 8000)
BIN_DIR = "bin" if os.name != "nt" else "Scripts"
PTY = True if os.name != "nt" else False

ACTIVE_VENV = os.environ.get("VIRTUAL_ENV", None)
VENV_HOME = Path(os.environ.get("WORKON_HOME", "~/.local/share/virtualenvs"))
VENV_PATH = Path(ACTIVE_VENV) if ACTIVE_VENV else (VENV_HOME / "kagi")
VENV = str(VENV_PATH.expanduser())
VENV_BIN = Path(VENV) / Path(BIN_DIR)

TOOLS = ["poetry", "pre-commit"]
POETRY = which("poetry") if which("poetry") else (VENV / Path("bin") / "poetry")
PRECOMMIT = (
    which("pre-commit") if which("pre-commit") else (VENV / Path("bin") / "pre-commit")
)


@task
def docs(c):
    """Build documentation"""
    c.run(f"{VENV_BIN}/sphinx-build docs docs/_build", pty=PTY)


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
        c.run(f"{VENV_BIN}/python manage.py runserver {DEMO_PORT} ", pty=PTY)


@task
def tests(c):
    """Run the test suite"""
    c.run(
        f"{VENV_BIN}/pytest -s --doctest-modules --cov-report term-missing "
        "--cov-fail-under 100 --cov kagi",
        pty=PTY,
    )


@task
def makemigrations(c):
    """Create database migrations if needed"""
    with cd("testproj"):
        c.run(f"{VENV_BIN}/python manage.py makemigrations", pty=PTY)


@task
def migrate(c):
    """Migrate database to current schema"""
    with cd("testproj"):
        c.run(f"{VENV_BIN}/python manage.py migrate", pty=PTY)


@task
def black(c, check=False, diff=False):
    """Run Black auto-formatter, optionally with --check or --diff"""
    diff_flag, check_flag = "", ""
    if check:
        check_flag = "--check"
    if diff:
        diff_flag = "--diff"
    c.run(f"{VENV_BIN}/black {check_flag} {diff_flag} kagi testproj tasks.py", pty=PTY)


@task
def isort(c, check=False):
    check_flag = ""
    if check:
        check_flag = "-c"
    c.run(f"{VENV_BIN}/isort {check_flag} .", pty=PTY)


@task
def flake8(c):
    c.run(f"{VENV_BIN}/flake8 kagi testproj tasks.py", pty=PTY)


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
            c.run(f"{VENV_BIN}/python -m pip install {tool}", pty=PTY)


@task
def precommit(c):
    """Install pre-commit hooks to .git/hooks/pre-commit"""
    c.run(f"{PRECOMMIT} install", pty=PTY)


@task
def setup(c):
    c.run(f"{VENV_BIN}/python -m pip install -U pip", pty=PTY)
    tools(c)
    c.run(f"{POETRY} install", pty=PTY)
    precommit(c)
