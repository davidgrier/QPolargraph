from PyQt5.QtWidgets import (QApplication, QMainWindow)
from PyQt5 import uic
from PyQt5.QtCore import (Qt, pyqtSignal, pyqtSlot)
from QInstrument.lib import Configure
import pyqtgraph as pg
import os
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
        self.config = Configure(configdir='~/.QScanner')
        self.restoreSettings()
        self._configurePlot()
        self._connectSignals()

    def closeEvent(self, event):
        logger.debug(f'Closing: {event.type()}')
        self.saveSettings()
        self.ui.polargraph.close()

    def _loadUi(self, uiFile):
        filename = os.path.join(os.path.dirname(__file__), uiFile)
        form, _ = uic.loadUiType(filename)
        # form, _ = uic.loadUiType(uiFile, import_from='QPolargraph')
        ui = form()
        ui.setupUi(self)
        return ui

    def _connectSignals(self):
        self.ui.scanner.propertyChanged.connect(self.handleChange)
        self.scanner.dataReady.connect(self.plotBelt)
        self.scanner.moveFinished.connect(self.motionFinished)
        self.scanner.scanFinished.connect(self.scanFinished)
        self.ui.home.clicked.connect(self.scanner.home)
        self.ui.center.clicked.connect(self.scanner.center)
        self.ui.scan.clicked.connect(self.handleScan)
        self.ui.actionSaveSettings.triggered.connect(self.saveSettings)
        self.ui.actionRestoreSettings.triggered.connect(self.restoreSettings)

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
        xp, yp, running = p.position if (data is None) else data
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
        # self.ui.controls.setEnabled(True)
        # self.ui.buttons.setEnabled(True)
        pass

    @pyqtSlot()
    def handleScan(self):
        if self.polargraph.running():
            self.statusBar().showMessage('Aborting scan')
            self.scanner.interrupt()
            self.ui.scan.setText('Stopping')
            self.ui.scan.setEnabled(False)
        else:
            self.statusBar().showMessage('Scanning...')
            self.ui.scan.setText('Stop')
            self.ui.polargraph.setEnabled(False)
            self.ui.scanner.setEnabled(False)
            self.scanner.scan()

    @pyqtSlot()
    def scanFinished(self):
        self.ui.scan.setText('Scan')
        self.ui.scan.setEnabled(True)
        self.ui.polargraph.setEnabled(True)
        self.ui.scanner.setEnabled(True)
        self.statusBar().showMessage('Scan complete')

    @pyqtSlot()
    def saveSettings(self):
        self.config.save(self.ui.scanner)
        self.config.save(self.ui.polargraph)
        self.statusBar().showMessage('Configuration saved')

    @pyqtSlot()
    def restoreSettings(self):
        self.config.restore(self.ui.scanner)
        self.config.restore(self.ui.polargraph)
        self.statusBar().showMessage('Configuration restored')


def main():
    import sys

    app = QApplication(sys.argv)
    widget = QScanner()
    widget.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
