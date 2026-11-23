import importlib
from importlib.metadata import version, PackageNotFoundError
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Type checkers cannot follow the lazy __getattr__ below.
    from .FlashFirmware import FlashDialog
    from .hardware.fake import FakeMotors, FakePolargraph
    from .hardware.Motors import Motors
    from .hardware.Polargraph import Polargraph
    from .hardware.QPolargraphWidget import QPolargraphWidget
    from .patterns.PolarScan import PolarScan
    from .patterns.QScanPattern import QScanPattern
    from .patterns.QScanPatternWidget import QScanPatternWidget
    from .patterns.RasterScan import RasterScan
    from .patterns.TarzanScan import TarzanScan
    from .patterns.TarzanScanWidget import TarzanScanWidget
    from .QScanner import QScanner

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
    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')


__all__ = list(_lazy)
