from PyQt5.QtWidgets import (QApplication, QMainWindow)
from PyQt5 import uic
from PyQt5.QtCore import (Qt, pyqtSignal, pyqtSlot)
import pyqtgraph as pg
import logging

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


class QScanner(QMainWindow):

    data = pyqtSignal(list)
    finished = pyqtSignal()

    def __init__(self, *args, **kwargs):
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        super().__init__(*args, **kwargs)
        self.ui = self._loadUi('Scanner.ui')
        self.polargraph = self.ui.polargraph.device
        self.scanner = self.ui.scanner.device
        self.scanner.polargraph = self.polargraph
        self._configurePlot()
        self._connectSignals()

    def closeEvent(self, event):
        logger.debug(f'Closing: {event.type()}')
        self.ui.polargraph.close()

    def _loadUi(self, uiFile):
        form, _ = uic.loadUiType(uiFile, import_from='QPolargraph')
        ui = form()
        ui.setupUi(self)
        return ui

    def _connectSignals(self):
        self.ui.scanner.propertyChanged.connect(self.handleChange)
        self.scanner.dataReady.connect(self.plotBelt)
        self.scanner.moveFinished.connect(self.motionFinished)
        self.ui.home.clicked.connect(self.handleSignal)
        self.ui.center.clicked.connect(self.handleSignal)
        self.ui.scan.clicked.connect(self.handleSignal)

    def _configurePlot(self):
        self.plot = pg.PlotItem()
        self.ui.graphicsView.setCentralItem(self.plot)
        self.plot.invertY(True)
        self.plot.setAspectLocked(ratio=1.)
        self.plot.showGrid(True, True, 0.2)

        pen = pg.mkPen('r', style=Qt.DotLine)
        self.trajectory = pg.PlotDataItem(pen=pen)
        self.plot.addItem(self.trajectory)
        self.plotTrajectory()

        pen = pg.mkPen('k', thick=3)
        brush = pg.mkBrush('y')
        self.belt = pg.PlotDataItem(pen=pen, symbol='o',
                                    symbolPen=pen, symbolBrush=brush)
        self.plot.addItem(self.belt)
        self.plotBelt()

    def plotTrajectory(self):
        x, y = self.scanner.trajectory()
        self.trajectory.setData(x, y)

    @pyqtSlot()
    @pyqtSlot(list)
    def plotBelt(self, data=None):
        p = self.polargraph
        xp, yp = p. position if (data is None) else data
        x = [-p.ell/2., xp, p.ell/2]
        y = [0, yp, 0]
        self.belt.setData(x, y)
        QApplication.processEvents()

    def plotData(self):
        pass

    @pyqtSlot(str, object)
    def handleChange(self, name, value):
        self.plotBelt()
        self.plotTrajectory()

    @pyqtSlot()
    def motionFinished(self):
        print('motion finished')
        #self.ui.controls.setEnabled(True)
        #self.ui.buttons.setEnabled(True)

    @pyqtSlot()
    def handleSignal(self):
        action = {self.ui.home: self.scanner.home,
                  self.ui.center: self.scanner.center,
                  self.ui.scan: self.scanner.scan}
        action[self.sender()]()
        #self.ui.controls.setEnabled(False)
        #self.ui.buttons.setEnabled(False)

    @pyqtSlot()
    def debug(self):
        print('scan requested')


def main():
    import sys

    app = QApplication(sys.argv)
    widget = QScanner()
    widget.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
