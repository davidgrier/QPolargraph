from pathlib import Path
from qtpy.QtWidgets import QApplication, QMainWindow
from qtpy import uic, QtCore
from qtpy.QtCore import Qt
from QInstrument.lib.Configure import Configure
import pyqtgraph as pg
import numpy as np
import inspect
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

    Class Attributes
    ----------------
    UIFILE : str
        Filename of the Qt Designer ``.ui`` file.  Subclasses may
        override this to provide a different layout while inheriting
        all scanner behaviour.

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

    UIFILE = 'Scanner.ui'

    def __init__(self, *args, configdir: str | None = None, **kwargs):
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        super().__init__(*args, **kwargs)
        uic.loadUi(self._uiPath(), self)
        self.showStatus = self.statusBar().showMessage
        self.scanner.device.polargraph = self.polargraph.device
        configdir = configdir or '~/.QScanner'
        self.config = Configure(configdir=configdir)
        self.restoreSettings()
        self._configurePlot()
        self._connectSignals()

    def closeEvent(self, event) -> None:
        logger.debug(f'Closing: {event.type()}')
        self.saveSettings()
        self.polargraph.device.close()

    @classmethod
    def _uiPath(cls) -> Path:
        '''Return the absolute path to this class's UI file.

        Resolves :attr:`UIFILE` relative to the directory of the class
        in the MRO that defines it, so subclasses that override
        :attr:`UIFILE` resolve correctly regardless of working directory.
        '''
        for klass in cls.__mro__:
            if 'UIFILE' in klass.__dict__:
                return Path(inspect.getfile(klass)).parent / klass.UIFILE
        raise AttributeError(f'{cls.__name__} has no UIFILE defined')

    def _connectSignals(self) -> None:
        self.scan.clicked.connect(self.toggleScan)
        self.polargraph.propertyChanged.connect(self.updatePlot)
        self.scanner.propertyChanged.connect(self.updatePlot)
        self.scanner.device.dataReady.connect(self.plotBelt)
        self.scanner.device.scanFinished.connect(self.scanFinished)
        self.home.clicked.connect(self.scanner.device.home)
        self.center.clicked.connect(self.scanner.device.center)
        self.actionSaveSettings.triggered.connect(self.saveSettings)
        self.actionRestoreSettings.triggered.connect(self.restoreSettings)

    def _configurePlot(self) -> None:
        self.plot = pg.PlotItem()
        self.graphicsView.setCentralItem(self.plot)
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
        x, y = self.scanner.device.trajectory()
        self.trajectoryPlot.setData(x, y)

    @QtCore.Slot()
    @QtCore.Slot(list)
    def plotBelt(self, data=None) -> None:
        p = self.polargraph.device
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
        if not self.polargraph.device.running():
            self.scanStarted()
        else:
            self.scanAborted()

    @QtCore.Slot()
    def scanStarted(self) -> None:
        self.showStatus('Scanning...')
        self.scan.setText('Stop')
        for w in [self.center, self.home, self.polargraph, self.scanner]:
            w.setEnabled(False)
        self.scanner.device.scan()

    @QtCore.Slot()
    def scanAborted(self) -> None:
        self.showStatus('Aborting scan')
        self.scanner.device.interrupt()
        self.scan.setText('Stopping')
        self.scan.setEnabled(False)

    @QtCore.Slot()
    def scanFinished(self) -> None:
        self.scan.setText('Scan')
        for w in [self.scan, self.center, self.home, self.polargraph, self.scanner]:
            w.setEnabled(True)
        self.showStatus('Scan complete')

    @QtCore.Slot()
    def saveSettings(self) -> None:
        self.config.save(self.scanner)
        self.config.save(self.polargraph)
        self.showStatus('Configuration saved')

    @QtCore.Slot()
    def restoreSettings(self) -> None:
        self.config.restore(self.scanner)
        self.config.restore(self.polargraph)
        self.showStatus('Configuration restored')

    @classmethod
    def example(cls) -> None:
        '''Launch the scanner application.

        Creates a ``QApplication``, instantiates the scanner, shows it,
        and runs the event loop.  Intended to be called from
        ``__main__`` in subclass modules:

        .. code-block:: python

            if __name__ == '__main__':
                QMyScanner.example()
        '''
        import sys

        app = QApplication.instance() or QApplication(sys.argv)
        widget = cls()
        widget.show()
        sys.exit(app.exec())


if __name__ == '__main__':
    QScanner.example()
