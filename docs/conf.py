import os

on_rtd = os.environ.get("READTHEDOCS", None) == "True"


# -- Project information -----------------------------------------------------

project = "Kagi"
copyright = "2019 – present, Justin Mayer & Rémy Hubscher"
author = "Justin Mayer & Rémy Hubscher"


# -- General configuration ---------------------------------------------------

extensions = ["sphinx.ext.autosectionlabel", "sphinx.ext.extlinks"]
templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------

html_theme = "default"
if not on_rtd:
    try:
        import sphinx_rtd_theme

        html_theme = "sphinx_rtd_theme"
        html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]
    except ImportError:
        pass

html_static_path = ["_static"]

# If false, no module index is generated.
html_use_modindex = False

# If false, no index is generated.
html_use_index = False

# If true, links to the reST sources are added to the pages.
html_show_sourcelink = False


# -- Extension Configuration -------------------------------------------------

extlinks = {"issue": ("https://github.com/justinmayer/kagi/issues/%s", "issue ")}
