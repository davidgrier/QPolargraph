from qtpy.QtWidgets import QApplication, QMainWindow
from qtpy import uic, QtCore
from qtpy.QtCore import Qt
from QInstrument.lib.Configure import Configure
import pyqtgraph as pg
import numpy as np
import os
import logging


logger = logging.getLogger(__name__)


class QScanner(QMainWindow):

    '''Application framework for a polargraph scanner.

    Loads the ``Scanner.ui`` layout, wires up a
    :class:`~QPolargraph.QPolargraphWidget.QPolargraphWidget` and a
    :class:`~QPolargraph.QRasterScanWidget.QRasterScanWidget`, and
    provides a live :mod:`pyqtgraph` display of the scan trajectory and
    current belt geometry. Intended to be subclassed for
    experiment-specific scanner applications.

    Properties
    ----------
    configdir : str
        Directory for storing instrument configuration.
        Default: ``~/.QScanner``.

    Methods
    -------
    showStatus(message)
        Display *message* on the status bar.
    plotData(x, y, hue)
        Add scatter points at ``(x, y)`` coloured by *hue* in ``[0, 1]``.

    Signals
    -------
    data(list)
        Emitted when data are ready; carries ``[x, y]`` [m].
    '''

    data = QtCore.Signal(list)

    uiFile = 'Scanner.ui'

    def __init__(self, *args, configdir: str | None = None, **kwargs):
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        super().__init__(*args, **kwargs)
        self.ui = self._loadUi(self.uiFile)
        self.showStatus = self.statusBar().showMessage
        self.polargraph = self.ui.polargraph.device
        self.scanner = self.ui.scanner.device
        self.scanner.polargraph = self.polargraph
        configdir = configdir or '~/.QScanner'
        self.config = Configure(configdir=configdir)
        self.restoreSettings()
        self._configurePlot()
        self._connectSignals()

    def closeEvent(self, event) -> None:
        logger.debug(f'Closing: {event.type()}')
        self.saveSettings()
        self.ui.polargraph.close()

    def _loadUi(self, uiFile: str):
        filename = os.path.join(os.path.dirname(__file__), uiFile)
        form, _ = uic.loadUiType(filename)
        ui = form()
        ui.setupUi(self)
        return ui

    def _connectSignals(self) -> None:
        self.ui.scan.clicked.connect(self.toggleScan)
        self.ui.polargraph.propertyChanged.connect(self.updatePlot)
        self.ui.scanner.propertyChanged.connect(self.updatePlot)
        self.scanner.dataReady.connect(self.plotBelt)
        self.scanner.scanFinished.connect(self.scanFinished)
        self.ui.home.clicked.connect(self.scanner.home)
        self.ui.center.clicked.connect(self.scanner.center)
        self.ui.actionSaveSettings.triggered.connect(self.saveSettings)
        self.ui.actionRestoreSettings.triggered.connect(self.restoreSettings)

    def _configurePlot(self) -> None:
        self.plot = pg.PlotItem()
        self.ui.graphicsView.setCentralItem(self.plot)
        self.plot.invertY(True)
        self.plot.setAspectLocked(ratio=1.)
        self.plot.showGrid(True, True, 0.2)

        pen = pg.mkPen('r', style=Qt.PenStyle.DotLine)
        self.trajectoryPlot = pg.PlotDataItem(pen=pen)
        self.plot.addItem(self.trajectoryPlot)
        self.plotTrajectory()

        pen = pg.mkPen('k', width=3)
        brush = pg.mkBrush('y')
        self.beltPlot = pg.PlotDataItem(pen=pen, symbol='o',
                                        symbolPen=pen, symbolBrush=brush)
        self.plot.addItem(self.beltPlot)
        self.plotBelt()

        self.dataPlot = pg.ScatterPlotItem(pen=None)
        self.plot.addItem(self.dataPlot)

    @QtCore.Slot(str, object)
    def updatePlot(self, name: str, value: object) -> None:
        self.plotTrajectory()
        self.plotBelt()

    @QtCore.Slot()
    def plotTrajectory(self) -> None:
        x, y = self.scanner.trajectory()
        self.trajectoryPlot.setData(x, y)

    @QtCore.Slot()
    @QtCore.Slot(list)
    def plotBelt(self, data=None) -> None:
        p = self.polargraph
        xp, yp, running = p.position if (data is None) else data
        x = [-p.ell / 2., xp, p.ell / 2]
        y = [0, yp, 0]
        self.beltPlot.setData(x, y)
        QApplication.processEvents()

    def plotData(self, x, y, hue) -> None:
        '''Add scatter points to the data plot.

        Parameters
        ----------
        x : array-like
            Horizontal coordinates [m].
        y : array-like
            Vertical coordinates [m].
        hue : array-like
            Colour values in ``[0, 1]`` (HSV hue).
        '''
        x = np.atleast_1d(x)
        y = np.atleast_1d(y)
        brush = [pg.hsvColor(h) for h in np.atleast_1d(hue)]
        self.dataPlot.addPoints(x, y, brush=brush)

    @QtCore.Slot()
    def toggleScan(self) -> None:
        if not self.polargraph.running():
            self.scanStarted()
        else:
            self.scanAborted()

    @QtCore.Slot()
    def scanStarted(self) -> None:
        self.showStatus('Scanning...')
        ui = self.ui
        ui.scan.setText('Stop')
        for w in [ui.center, ui.home, ui.polargraph, ui.scanner]:
            w.setEnabled(False)
        self.scanner.scan()

    @QtCore.Slot()
    def scanAborted(self) -> None:
        self.showStatus('Aborting scan')
        self.scanner.interrupt()
        self.ui.scan.setText('Stopping')
        self.ui.scan.setEnabled(False)

    @QtCore.Slot()
    def scanFinished(self) -> None:
        ui = self.ui
        ui.scan.setText('Scan')
        for w in [ui.scan, ui.center, ui.home, ui.polargraph, ui.scanner]:
            w.setEnabled(True)
        self.showStatus('Scan complete')

    @QtCore.Slot()
    def saveSettings(self) -> None:
        self.config.save(self.ui.scanner)
        self.config.save(self.ui.polargraph)
        self.showStatus('Configuration saved')

    @QtCore.Slot()
    def restoreSettings(self) -> None:
        self.config.restore(self.ui.scanner)
        self.config.restore(self.ui.polargraph)
        self.showStatus('Configuration restored')


def main():
    import sys

    app = QApplication(sys.argv)
    widget = QScanner()
    widget.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
