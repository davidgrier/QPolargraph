from pathlib import Path
import inspect
from qtpy import QtCore, QtWidgets
from qtpy import uic
from QPolargraph.PolarScan import PolarScan


class QRasterScanWidget(QtWidgets.QWidget):

    '''Widget for controlling the scan-pattern parameters.

    Wraps a :class:`~QPolargraph.PolarScan.PolarScan` device (default)
    in the ``RasterScanWidget.ui`` layout, with direct spinbox-to-property
    bindings.

    Signals
    -------
    patternChanged()
        Emitted whenever a scan parameter is changed by the user.
    '''

    patternChanged = QtCore.Signal()

    UIFILE = 'RasterScanWidget.ui'

    def __init__(self, *args, device=None, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi(self._uiPath(), self)
        self.device = device or PolarScan()
        self._syncFromDevice()
        self._connectSignals()

    @classmethod
    def _uiPath(cls) -> Path:
        for klass in cls.__mro__:
            if 'UIFILE' in klass.__dict__:
                return Path(inspect.getfile(klass)).parent / klass.UIFILE
        raise AttributeError(f'{cls.__name__} has no UIFILE defined')

    def _syncFromDevice(self) -> None:
        for name in ('width', 'height', 'dx', 'dy', 'step'):
            widget = getattr(self, name)
            with QtCore.QSignalBlocker(widget):
                widget.setValue(getattr(self.device, name))

    def _connectSignals(self) -> None:
        for name in ('width', 'height', 'dx', 'dy', 'step'):
            getattr(self, name).valueChanged.connect(self._updateDevice)

    def _updateDevice(self) -> None:
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
    QRasterScanWidget.example()
