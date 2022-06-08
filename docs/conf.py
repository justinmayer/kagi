import datetime
import os

on_rtd = os.environ.get("READTHEDOCS", None) == "True"


# -- Project information -----------------------------------------------------

project = "Kagi"
year = datetime.datetime.now().date().year
copyright = f"2019–{year} Justin Mayer & Rémy Hubscher"
author = "Justin Mayer & Rémy Hubscher"


# -- General configuration ---------------------------------------------------

extensions = ["sphinx.ext.autosectionlabel", "sphinx.ext.extlinks"]
templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
master_doc = "index"

# -- Options for HTML output -------------------------------------------------

html_title = "Kagi Docs"

html_theme = "default"
try:
    import furo  # NOQA

    html_theme = "furo"
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

extlinks = {
    "issue": ("https://github.com/justinmayer/kagi/issues/%s", "issue "),
    "github": ("https://github.com/%s/", ""),
    "rtd": ("https://%s.readthedocs.io", ""),
}
