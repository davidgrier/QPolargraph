from QInstrument.lib import QInstrumentWidget
from QPolargraph.Polargraph import Polargraph
from PyQt5.QtCore import QThread
import logging


logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class QPolargraphWidget(QInstrumentWidget):
    '''Polargraph scanner
    '''

    def __init__(self, *args, **kwargs):
        device = Polargraph().find()
        super().__init__(*args,
                         uiFile='PolargraphWidget.ui',
                         device=device,
                         **kwargs)
        self._thread = QThread(self)
        self.device.moveToThread(self._thread)
        self._thread.start()

    def closeEvent(self, event):
        logger.debug(f'Closing: {event.type()}')
        self._thread.quit()
        self._thread.wait()
        del self._thread
        del self._device
        super().closeEvent(event)
        event.accept()


def main():
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    widget = QPolargraphWidget()
    widget.show()
    print(widget.get('ell'))
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
