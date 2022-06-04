from PyQt5.QtWidgets import QMainWindow
from PyQt5 import uic
import pyqtgraph as pg
import logging

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class QScanner(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        self.ui = self._loadUi('Scanner.ui')

    def _loadUi(self, uiFile):
        form, _ = uic.loadUiType(uiFile, self, 'QPolargraph')
        ui = form()
        ui.setupUi(self)
        return ui

    def closeEvent(self, event):
        logger.debug(f'Closing: {event.type()}')
        self.ui.polargraph.close()


def main():
    from PyQt5.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    widget = QScanner()
    widget.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
