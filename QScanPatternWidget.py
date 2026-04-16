from pathlib import Path
import inspect
from qtpy import QtCore, QtWidgets
from qtpy import uic
from QPolargraph.PolarScan import PolarScan


class QScanPatternWidget(QtWidgets.QWidget):

    '''Widget for controlling the scan-pattern parameters.

    Wraps a :class:`~QPolargraph.QScanPattern.QScanPattern` device in
    the ``RasterScanWidget.ui`` layout, with direct spinbox-to-property
    bindings.  The default device is
    :class:`~QPolargraph.PolarScan.PolarScan`; pass a different
    :class:`~QPolargraph.QScanPattern.QScanPattern` subclass instance
    to ``device`` to use a different scan pattern.

    Signals
    -------
    patternChanged()
        Emitted whenever a scan parameter is changed by the user.
    '''

    patternChanged = QtCore.Signal()

    UIFILE = 'RasterScanWidget.ui'

    def __init__(self, *args, device=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._device = None
        uic.loadUi(self._uiPath(), self)
        self._connectSignals()
        self.device = device or PolarScan()

    @classmethod
    def _uiPath(cls) -> Path:
        for klass in cls.__mro__:
            if 'UIFILE' in klass.__dict__:
                return Path(inspect.getfile(klass)).parent / klass.UIFILE
        raise AttributeError(f'{cls.__name__} has no UIFILE defined')

    @property
    def device(self):
        '''The scan pattern controlled by this widget.'''
        return self._device

    @device.setter
    def device(self, value) -> None:
        self._device = value
        if value is not None:
            self._syncFromDevice()

    def _syncFromDevice(self) -> None:
        for name in ('width', 'height', 'dx', 'dy', 'step'):
            widget = getattr(self, name)
            with QtCore.QSignalBlocker(widget):
                widget.setValue(getattr(self.device, name))

    def _connectSignals(self) -> None:
        for name in ('width', 'height', 'dx', 'dy', 'step'):
            getattr(self, name).valueChanged.connect(self._updateDevice)

    def _updateDevice(self) -> None:
        if self._device is None:
            return
        for name in ('width', 'height', 'dx', 'dy', 'step'):
            setattr(self.device, name, getattr(self, name).value())
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
        self._updateDevice()

    @classmethod
    def example(cls) -> None:
        import sys
        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
        widget = cls()
        widget.show()
        sys.exit(app.exec())


if __name__ == '__main__':
    QScanPatternWidget.example()
