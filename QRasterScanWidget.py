from QInstrument.lib.QInstrumentWidget import QInstrumentWidget
from QPolargraph.PolarScan import PolarScan


class QRasterScanWidget(QInstrumentWidget):

    '''Widget for controlling the scan-pattern parameters.

    Wraps a :class:`~QPolargraph.PolarScan.PolarScan` device (default)
    in the ``RasterScanWidget.ui`` layout.
    '''

    UIFILE = 'RasterScanWidget.ui'

    def __init__(self, *args, device=None, **kwargs):
        super().__init__(*args, device=device or PolarScan(), **kwargs)


if __name__ == '__main__':
    QRasterScanWidget.example()
