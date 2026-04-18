from qtpy import QtCore
from QPolargraph.patterns.QScanPatternWidget import QScanPatternWidget
from QPolargraph.patterns.TarzanScan import TarzanScan


class TarzanScanWidget(QScanPatternWidget):

    '''Widget for controlling Tarzan scan parameters.

    Extends :class:`~QPolargraph.QScanPatternWidget.QScanPatternWidget`
    with an ``x₀`` spinbox for setting the starting x-position on the
    top edge of the scan area.

    The default pattern is
    :class:`~QPolargraph.TarzanScan.TarzanScan`.
    '''

    UIFILE = 'TarzanScanWidget.ui'

    def __init__(self, *args, pattern=None, **kwargs):
        super().__init__(*args, pattern=pattern or TarzanScan(), **kwargs)

    def _syncFromPattern(self) -> None:
        super()._syncFromPattern()
        with QtCore.QSignalBlocker(self.x0):
            self.x0.setValue(self.pattern.x0)

    def _connectSignals(self) -> None:
        super()._connectSignals()
        self.x0.valueChanged.connect(self._updatePattern)

    def _updatePattern(self) -> None:
        if self._pattern is None:
            return
        for name in ('width', 'height', 'dx', 'dy', 'step'):
            setattr(self.pattern, name, getattr(self, name).value())
        self.pattern.x0 = self.x0.value()
        self.patternChanged.emit()

    @property
    def settings(self) -> dict:
        '''Current scan parameter values, suitable for save/restore.'''
        return super().settings | {'x0': self.x0.value()}

    @settings.setter
    def settings(self, values: dict) -> None:
        if 'x0' in values:
            with QtCore.QSignalBlocker(self.x0):
                self.x0.setValue(float(values['x0']))
        QScanPatternWidget.settings.fset(self, values)


if __name__ == '__main__':
    TarzanScanWidget.example()
