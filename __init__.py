import importlib
from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version('QPolargraph')
except PackageNotFoundError:
    __version__ = None

_lazy = {
    'Motors':             'Motors',
    'Polargraph':         'Polargraph',
    'FakeMotors':         'fake',
    'FakePolargraph':     'fake',
    'QPolargraphWidget':  'QPolargraphWidget',
    'QScanPatternWidget': 'QScanPatternWidget',
    'QScanner':           'QScanner',
    'QScanPattern':       'QScanPattern',
    'RasterScan':         'RasterScan',
    'PolarScan':          'PolarScan',
}


def __getattr__(name):
    if name in _lazy:
        mod = importlib.import_module(f'.{_lazy[name]}', package=__name__)
        return getattr(mod, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = list(_lazy)
