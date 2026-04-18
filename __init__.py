import importlib
from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version('QPolargraph')
except PackageNotFoundError:
    __version__ = None

_lazy = {
    'Motors':             'hardware.Motors',
    'Polargraph':         'hardware.Polargraph',
    'FakeMotors':         'hardware.fake',
    'FakePolargraph':     'hardware.fake',
    'QPolargraphWidget':  'hardware.QPolargraphWidget',
    'QScanPatternWidget': 'patterns.QScanPatternWidget',
    'TarzanScanWidget':   'patterns.TarzanScanWidget',
    'QScanner':           'QScanner',
    'FlashDialog':        'FlashFirmware',
    'QScanPattern':       'patterns.QScanPattern',
    'RasterScan':         'patterns.RasterScan',
    'PolarScan':          'patterns.PolarScan',
    'TarzanScan':         'patterns.TarzanScan',
}


def __getattr__(name):
    if name in _lazy:
        mod = importlib.import_module(f'.{_lazy[name]}', package=__name__)
        value = getattr(mod, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = list(_lazy)
