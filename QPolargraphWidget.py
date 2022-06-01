from QInstrument.lib import QInstrumentWidget
from QPolargraph.Polargraph import Polargraph
from PyQt5.QtCore import pyqtSlot


class QPolargraphWidget(QInstrumentWidget):
    '''Polargraph scanner
    '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args,
                         uiFile='PolargraphWidget.ui',
                         deviceClass=Polargraph,
                         **kwargs)


def main():
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    widget = QPolargraphWidget()
    widget.show()
    print(widget.properties)
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
