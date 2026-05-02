from __future__ import annotations

from dataclasses import dataclass
from qtpy import QtCore, QtWidgets
from QPolargraph.patterns.PolarScan import PolarScan
from QPolargraph.patterns.QScanPattern import QScanPattern


@dataclass
class FieldSpec:
    '''Specification for a single spinbox field in a scan pattern widget.

    Parameters
    ----------
    name : str
        Attribute name on both the widget and the scan pattern.
    label : str
        Display text for the label widget.
    suffix : str
        Spinbox suffix string (e.g. ``' m'``, ``' mm'``).
    minimum : float
        Spinbox minimum value.
    maximum : float
        Spinbox maximum value.
    single_step : float
        Spinbox increment per step.
    value : float
        Default value.
    decimals : int
        Number of decimal places displayed.  Default: 2.
    tooltip : str
        Optional tooltip text for the spinbox.  Default: empty.
    '''
    name: str
    label: str
    suffix: str
    minimum: float
    maximum: float
    single_step: float
    value: float
    decimals: int = 2
    tooltip: str = ''


class QScanPatternWidget(QtWidgets.QWidget):

    '''Widget for controlling scan-pattern parameters.

    Builds a compact grid of label/spinbox pairs from :attr:`_FIELD_SPECS`
    and keeps them in sync with a
    :class:`~QPolargraph.QScanPattern.QScanPattern` instance.
    Subclasses extend :attr:`_FIELD_SPECS` to add fields without needing
    a separate ``.ui`` file:

    .. code-block:: python

        class MyWidget(QScanPatternWidget):
            _FIELD_SPECS = QScanPatternWidget._FIELD_SPECS + [
                FieldSpec('x0', 'x₀', ' m', -1., 1., 0.001, 0.),
            ]

    Signals
    -------
    patternChanged()
        Emitted whenever a scan parameter is changed by the user.
    '''

    patternChanged = QtCore.Signal()

    _FIELD_SPECS: list[FieldSpec] = [
        FieldSpec('width',  'width',   ' m',  0.1, 10.0, 0.01, 0.6),
        FieldSpec('height', 'height',  ' m',  0.1, 10.0, 0.01, 0.6),
        FieldSpec('dx',     'Δx',      ' m', -1.0,  1.0, 0.01, 0.0),
        FieldSpec('dy',     'Δy',      ' m', -1.0,  1.0, 0.01, 0.1),
        FieldSpec('step',   'step',    ' mm', 1.0, 100.0, 1.0,  5.0,
                  decimals=1),
    ]

    def __init__(self, *args,
                 pattern: QScanPattern | None = None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self._pattern = None
        self.setupUi()
        self._connectSignals()
        self.pattern = pattern or PolarScan()

    def setupUi(self) -> None:
        layout = QtWidgets.QGridLayout(self)
        layout.setContentsMargins(2, 1, 2, 1)
        layout.setHorizontalSpacing(6)
        layout.setVerticalSpacing(1)
        for i, spec in enumerate(self._FIELD_SPECS):
            row, col = divmod(i, 2)
            label = QtWidgets.QLabel(spec.label)
            label.setAlignment(
                QtCore.Qt.AlignmentFlag.AlignRight |
                QtCore.Qt.AlignmentFlag.AlignVCenter)
            spinbox = QtWidgets.QDoubleSpinBox()
            spinbox.setSuffix(spec.suffix)
            spinbox.setMinimum(spec.minimum)
            spinbox.setMaximum(spec.maximum)
            spinbox.setSingleStep(spec.single_step)
            spinbox.setDecimals(spec.decimals)
            spinbox.setValue(spec.value)
            spinbox.setSizePolicy(
                QtWidgets.QSizePolicy.Policy.Expanding,
                QtWidgets.QSizePolicy.Policy.Fixed)
            if spec.tooltip:
                spinbox.setToolTip(spec.tooltip)
            label.setBuddy(spinbox)
            layout.addWidget(label,   row, col * 2)
            layout.addWidget(spinbox, row, col * 2 + 1)
            setattr(self, spec.name, spinbox)

    @property
    def pattern(self) -> QScanPattern | None:
        '''The scan pattern controlled by this widget.'''
        return self._pattern

    @pattern.setter
    def pattern(self, value: QScanPattern | None) -> None:
        self._pattern = value
        if value is not None:
            self._syncFromPattern()

    def _syncFromPattern(self) -> None:
        for spec in self._FIELD_SPECS:
            widget = getattr(self, spec.name)
            with QtCore.QSignalBlocker(widget):
                widget.setValue(getattr(self.pattern, spec.name))

    def _connectSignals(self) -> None:
        for spec in self._FIELD_SPECS:
            signal = getattr(self, spec.name).valueChanged
            signal.connect(self._updatePattern)

    def _updatePattern(self) -> None:
        if self._pattern is None:
            return
        for spec in self._FIELD_SPECS:
            setattr(self.pattern, spec.name,
                    getattr(self, spec.name).value())
        self.patternChanged.emit()

    @property
    def settings(self) -> dict:
        '''Current scan parameter values, suitable for save/restore.'''
        return {spec.name: getattr(self, spec.name).value()
                for spec in self._FIELD_SPECS}

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
