'''Sphinx configuration for QPolargraph.'''

import os
import sys
from pathlib import Path

# Use Qt's offscreen platform so Qt classes can be imported by autodoc
# without a display (required on ReadTheDocs and other headless build hosts).
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

# The repo root is one level up from docs/.  Adding it to sys.path lets
# autodoc import QPolargraph without requiring an editable install.
sys.path.insert(0, str(Path(__file__).parent.parent))

# -- Project information -----------------------------------------------------

project = 'QPolargraph'
author = 'David G. Grier'
copyright = '2018\u20132026, David G. Grier'
from importlib.metadata import version as _get_version, PackageNotFoundError
try:
    release = _get_version('QPolargraph')
except PackageNotFoundError:
    release = '1.0.0'

# -- General configuration ---------------------------------------------------

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
    'sphinx.ext.viewcode',
    'sphinx_autodoc_typehints',
]

# Napoleon settings for NumPy-style docstrings
napoleon_numpy_docstring = True
napoleon_google_docstring = False
napoleon_use_param = False
napoleon_use_rtype = False

# autodoc settings
autodoc_member_order = 'bysource'
autodoc_default_options = {
    'undoc-members': False,
    'show-inheritance': True,
}

# Qt and scientific stack are not available on the RTD build server;
# mock all external imports.
autodoc_mock_imports = [
    'PyQt5',
    'PyQt6',
    'PySide2',
    'PySide6',
    'qtpy',
    'numpy',
    'pyqtgraph',
    'parse',
    'QInstrument',
]

# intersphinx: link to external package docs
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'numpy': ('https://numpy.org/doc/stable', None),
}

# -- Suppress duplicate-object warnings from Sphinx 8.x ---------------------

def _skip_signal_docstring(app, what, name, obj, options, lines):
    '''Suppress auto-generated signal docstrings (empty or mock artefacts).'''
    try:
        from PyQt6.QtCore import pyqtSignal
        if isinstance(obj, pyqtSignal):
            lines.clear()
            return
    except ImportError:
        pass
    try:
        from unittest.mock import NonCallableMock
        if isinstance(obj, NonCallableMock):
            lines.clear()
    except ImportError:
        pass


def setup(app):
    '''Suppress spurious duplicate-object warnings from Sphinx 8.x.'''
    from sphinx.domains.python import PythonDomain
    _orig = PythonDomain.note_object
    _seen = {}

    def _dedup(self, name, objtype, node_id, aliased=False, location=None):
        if not aliased and name in _seen:
            return _orig(self, name, objtype, node_id, aliased=True,
                         location=location)
        if not aliased:
            _seen[name] = self.env.docname
        return _orig(self, name, objtype, node_id, aliased, location)

    PythonDomain.note_object = _dedup
    app.connect('autodoc-process-docstring', _skip_signal_docstring)

# -- HTML output -------------------------------------------------------------

html_theme = 'pydata_sphinx_theme'
html_title = 'QPolargraph'
html_static_path = ['_static']
html_css_files = ['nyu.css']

html_theme_options = {
    'github_url': 'https://github.com/davidgrier/QPolargraph',
    'show_toc_level': 2,
    'navigation_with_keys': True,
    'show_nav_level': 2,
    'navbar_end': ['navbar-icon-links', 'theme-switcher'],
    'footer_start': ['copyright'],
    'footer_end': ['sphinx-version'],
}

html_sidebars = {'**': []}
