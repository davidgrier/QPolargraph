from QInstrument.lib import QInstrumentWidget
from QPolargraph.PolarScan import PolarScan as Pattern


class QRasterScanWidget(QInstrumentWidget):

    def __init__(self, *args, pattern=None, **kwargs):
        pattern = pattern or Pattern()
        super().__init__(*args,
                         device=pattern,
                         uiFile='RasterScanWidget.ui',
                         **kwargs)
        self.polargraph = self.device.polargraph


def main():
    from PyQt5.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    scanner = QRasterScanWidget()
    scanner.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

