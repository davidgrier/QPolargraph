from __future__ import annotations

from QPolargraph.patterns.QScanPatternWidget import FieldSpec, QScanPatternWidget
from QPolargraph.patterns.TarzanScan import TarzanScan


class TarzanScanWidget(QScanPatternWidget):

    '''Widget for controlling Tarzan scan parameters.

    Extends :class:`~QPolargraph.QScanPatternWidget.QScanPatternWidget`
    with an ``x₀`` spinbox for setting the starting x-position on the
    top edge of the scan area.  The default pattern is
    :class:`~QPolargraph.TarzanScan.TarzanScan`.
    '''

    _FIELD_SPECS = QScanPatternWidget._FIELD_SPECS + [
        FieldSpec('x0', 'x₀', ' m', -1.0, 1.0, 0.001, 0.0, decimals=3,
                  tooltip='Starting x-position on the top edge of the scan area'),
    ]

    def __init__(self, *args, pattern=None, **kwargs):
        super().__init__(*args, pattern=pattern, **kwargs)


if __name__ == '__main__':
    import sys
    from qtpy import QtWidgets
    from QPolargraph.hardware.fake import FakePolargraph
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    w = TarzanScanWidget(pattern=TarzanScan(polargraph=FakePolargraph()))
    w.show()
    sys.exit(app.exec())
