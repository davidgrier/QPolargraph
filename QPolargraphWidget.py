from QInstrument.lib import QInstrumentWidget
from QPolargraph import QPolargraph


class QPolargraphWidget(QInstrumentWidget):
    '''Polargraph scanner
    '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args,
                         uiFile='PolargraphWidget.ui',
                         deviceClass=QPolargraph,
                         **kwargs)


def main():
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    widget = QPolargraphWidget()
    widget.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
