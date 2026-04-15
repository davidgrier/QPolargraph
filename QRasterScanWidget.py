from QInstrument.lib.QInstrumentWidget import QInstrumentWidget
from QPolargraph.PolarScan import PolarScan as Pattern


class QRasterScanWidget(QInstrumentWidget):

    '''Widget for controlling the scan-pattern parameters.

    Wraps a :class:`~QPolargraph.PolarScan.PolarScan` device (default)
    in the ``RasterScanWidget.ui`` layout. The ``polargraph`` attribute
    mirrors the device's polargraph reference for convenience.
    '''

    def __init__(self, *args, pattern=None, **kwargs):
        pattern = pattern or Pattern()
        super().__init__(*args,
                         device=pattern,
                         uiFile='RasterScanWidget.ui',
                         **kwargs)
        self.polargraph = self.device.polargraph


def main():
    from qtpy.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    scanner = QRasterScanWidget()
    scanner.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
