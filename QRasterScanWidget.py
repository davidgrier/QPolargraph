from QInstrument.lib import QThreadedInstrumentWidget
from QPolargraph.RasterScan import RasterScan


class QRasterScanWidget(QThreadedInstrumentWidget):

    def __init__(self, *args, **kwargs):
        device = RasterScan()
        super().__init__(*args,
                         device=device,
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

