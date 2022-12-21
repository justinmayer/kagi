Contributing
============

We welcome your contributions to Kagi and strive to make it as easy as possible
to participate.

Quick Set-up
------------

First, install Poetry_::

    curl -sSL https://install.python-poetry.org/ | python -

Go to the `Kagi repository`_ on GitHub and tap the **Fork** button at top-right.
Then clone the source for your fork and add the upstream project as a Git remote::

    git clone https://github.com/YOUR_USERNAME/kagi.git
    cd kagi
    git remote add upstream https://github.com/justinmayer/kagi.git

Install dependencies and set up the project::

    poetry install
    poetry shell
    invoke setup

Your local environment should now be ready to go!

Detailed Set-up
---------------

.. highlight:: none

The first step is to install Poetry_::

    curl -sSL https://install.python-poetry.org/ | python -

Next, install Pre-commit_. Here we will install Pipx_ and use it to install Pre-commit_::

    python3 -m pip install --user pipx
    python3 -m pipx ensurepath
    pipx install pre-commit

Tell Pre-commit_ where to store its Git hooks, such as ``~/.local/share/git/templates``.
This only needs to be done once per workstation, so if you have already run these
commands for another project, you can skip this step::

    mkdir -p ~/.local/share/git/templates
    git config --global init.templateDir ~/.local/share/git/templates
    pre-commit init-templatedir ~/.local/share/git/templates

Go to the `Kagi repository`_ on GitHub and tap the **Fork** button at top-right.
Then clone the source for your fork and add the upstream project as a Git remote::

    git clone https://github.com/YOUR_USERNAME/kagi.git
    cd kagi
    git remote add upstream https://github.com/justinmayer/kagi.git

Install the Pre-commit_ hooks::

    pre-commit install

**(optional)** Poetry will automatically create a virtual environment for you but
will alternatively use an already-activated environment if you prefer to create
and activate your virtual environments manually::

    python3 -m venv ~/virtualenvs/kagi
    source ~/virtualenvs/kagi/bin/activate

Install Kagi and its dependencies via Poetry_::

    poetry install

Your local environment should now be ready to go. Use the following command to
run the test suite (you can omit ``poetry shell`` if you manually created and
activated a virtual environment via the optional step above)::

    poetry shell
    invoke tests

You can speed up test runs via the following command, replacing ``4`` with your
workstation’s CPU core count::

    PYTEST_ADDOPTS="-n 4" invoke tests

.. Links

.. _`Kagi repository`: https://github.com/justinmayer/kagi
.. _Pipx: https://pipxproject.github.io/pipx/installation/
.. _Poetry: https://poetry.eustace.io/docs/#installation
.. _Pre-commit: https://pre-commit.com/
