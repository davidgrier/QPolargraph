from QInstrument.lib import QThreadedInstrumentWidget
from QPolargraph.Polargraph import Polargraph


class QPolargraphWidget(QThreadedInstrumentWidget):
    '''Polargraph scanner
    '''

    def __init__(self, *args, **kwargs):
        device = Polargraph().find()
        super().__init__(*args,
                         uiFile='PolargraphWidget.ui',
                         device=device,
                         **kwargs)


def main():
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    polargraph = QPolargraphWidget()
    polargraph.show()
    print(f'Pulley separation: {polargraph.get("ell")} m')
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
