from pathlib import Path
import inspect
from qtpy import QtCore, QtWidgets
from qtpy import uic
from QPolargraph.PolarScan import PolarScan


class QScanPatternWidget(QtWidgets.QWidget):

    '''Widget for controlling the scan-pattern parameters.

    Wraps a :class:`~QPolargraph.QScanPattern.QScanPattern` instance in
    the ``RasterScanWidget.ui`` layout, with direct spinbox-to-property
    bindings.  The default pattern is
    :class:`~QPolargraph.PolarScan.PolarScan`; pass a different
    :class:`~QPolargraph.QScanPattern.QScanPattern` subclass instance
    to ``pattern`` to use a different scan pattern.

    Signals
    -------
    patternChanged()
        Emitted whenever a scan parameter is changed by the user.
    '''

    patternChanged = QtCore.Signal()

    UIFILE = 'RasterScanWidget.ui'
    _UIPATH = Path(__file__).parent / UIFILE

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if 'UIFILE' in cls.__dict__:
            cls._UIPATH = Path(inspect.getfile(cls)).parent / cls.UIFILE

    def __init__(self, *args, pattern=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._pattern = None
        uic.loadUi(self._UIPATH, self)
        self._connectSignals()
        self.pattern = pattern or PolarScan()

    @property
    def pattern(self):
        '''The scan pattern controlled by this widget.'''
        return self._pattern

    @pattern.setter
    def pattern(self, value) -> None:
        self._pattern = value
        if value is not None:
            self._syncFromPattern()

    def _syncFromPattern(self) -> None:
        for name in ('width', 'height', 'dx', 'dy', 'step'):
            widget = getattr(self, name)
            with QtCore.QSignalBlocker(widget):
                widget.setValue(getattr(self.pattern, name))

    def _connectSignals(self) -> None:
        for name in ('width', 'height', 'dx', 'dy', 'step'):
            getattr(self, name).valueChanged.connect(self._updatePattern)

    def _updatePattern(self) -> None:
        if self._pattern is None:
            return
        for name in ('width', 'height', 'dx', 'dy', 'step'):
            setattr(self.pattern, name, getattr(self, name).value())
        self.patternChanged.emit()

    @property
    def settings(self) -> dict:
        '''Current scan parameter values, suitable for save/restore.'''
        return {name: getattr(self, name).value()
                for name in ('width', 'height', 'dx', 'dy', 'step')}

    @settings.setter
    def settings(self, values: dict) -> None:
        for name, value in values.items():
            widget = getattr(self, name, None)
            if isinstance(widget, QtWidgets.QDoubleSpinBox):
                with QtCore.QSignalBlocker(widget):
                    widget.setValue(float(value))
        self._updatePattern()

    @classmethod
    def example(cls) -> None:
        import sys
        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
        widget = cls()
        widget.show()
        sys.exit(app.exec())


if __name__ == '__main__':
    QScanPatternWidget.example()
