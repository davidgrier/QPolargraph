from QInstrument.lib import QInstrumentWidget
from QPolargraph import QPolargraph
from PyQt5.QtCore import pyqtSlot


class QPolargraphWidget(QInstrumentWidget):
    '''Polargraph scanner
    '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args,
                         uiFile='PolargraphWidget.ui',
                         deviceClass=QPolargraph,
                         **kwargs)
        self.connectSignals()

    def connectSignals(self):
        self.ui.ell.valueChanged.connect(self.limitRange)

    @pyqtSlot(float)
    def limitRange(self, value):
        self.ui.width.setMaximum(0.9*value)
        self.ui.height.setMaximum(0.9*value)


def main():
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    widget = QPolargraphWidget()
    widget.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
