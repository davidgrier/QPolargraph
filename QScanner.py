# TODO
# add a "scan pattern" widget that allows the user to select and configure
# different scan patterns from the GUI, without needing to subclass QScanner.
# UI improvements
from __future__ import annotations

from pathlib import Path
from qtpy import uic, QtCore, QtGui, QtWidgets
from QInstrument.lib.Configure import Configure
from QPolargraph.hardware.QPolargraphWidget import QPolargraphWidget
from QPolargraph.patterns.QScanPattern import QScanPattern
from QPolargraph.patterns.PolarScan import PolarScan
from QPolargraph.patterns.RasterScan import RasterScan
from QPolargraph.patterns.TarzanScan import TarzanScan
import pyqtgraph as pg
import numpy as np
import numpy.typing as npt
import inspect
import logging


logger = logging.getLogger(__name__)


class QScanner(QtWidgets.QMainWindow):

    '''Application framework for a polargraph scanner.

    Loads the ``Scanner.ui`` layout, wires up a
    :class:`~QPolargraph.QPolargraphWidget.QPolargraphWidget` and a
    :class:`~QPolargraph.QScanPatternWidget.QScanPatternWidget`, and
    provides a live :mod:`pyqtgraph` display of the scan trajectory and
    current belt geometry. Intended to be subclassed for
    experiment-specific scanner applications.

    Class Attributes
    ----------------
    UIFILE : str
        Filename of the Qt Designer ``.ui`` file.  Subclasses may
        override this to provide a different layout while inheriting
        all scanner behavior.
    SCAN_PATTERN : type
        :class:`~QPolargraph.QScanPattern.QScanPattern` subclass to
        instantiate as the scan device.  Default:
        :class:`~QPolargraph.PolarScan.PolarScan`.  Subclasses override
        this to select a different scan pattern:

        .. code-block:: python

            class QMyScanner(QScanner):
                SCAN_PATTERN = RasterScan

    Properties
    ----------
    configdir : str
        Directory for storing instrument configuration.
        Defaults to ``~/.<ClassName>`` where *ClassName* is the name of
        the concrete subclass, so each subclass gets its own config directory.

    Methods
    -------
    showStatus(message)
        Display *message* on the status bar.
    plotData(x, y, hue)
        Add scatter points at ``(x, y)`` colored by *hue* in ``[0, 1]``.

    Signals
    -------
    dataReady(dict)
        Emitted at each position during a scan.  The base class emits
        ``{'x': float, 'y': float}`` [m].  Subclasses may override
        :meth:`_onDataReady` to merge in additional measurement fields
        before emitting, e.g.::

            def _onDataReady(self, pos: np.ndarray) -> None:
                self.plotBelt(pos)
                self.dataReady.emit(
                    {'x': float(pos[0]), 'y': float(pos[1])}
                    | self.instrument.acquire())

        A sequence of emitted dicts can be collected directly into a
        :class:`pandas.DataFrame`::

            rows = []
            scanner.dataReady.connect(rows.append)
            # after scan:
            df = pd.DataFrame(rows)
    '''

    dataReady = QtCore.Signal(dict)

    SCAN_PATTERN = PolarScan
    UIFILE = 'Scanner.ui'
    _UIPATH = Path(__file__).parent / UIFILE
    _SCAN_LOCKED = ('center', 'home', 'polargraph', 'scanner')

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if 'UIFILE' in cls.__dict__:
            cls._UIPATH = Path(inspect.getfile(cls)).parent / cls.UIFILE

    def __init__(self, *args, configdir: str | None = None,
                 fake: bool = False,
                 pattern: type | None = None, **kwargs):
        self._configurePyqtgraph()
        super().__init__(*args, **kwargs)
        QPolargraphWidget._fake = fake
        uic.loadUi(self._UIPATH, self)
        QPolargraphWidget._fake = False
        self._latestPosition: np.ndarray | None = None
        self._beltTimer = QtCore.QTimer(self)
        self._beltTimer.setInterval(33)  # ~30 Hz
        self._beltTimer.timeout.connect(self._updateBelt)
        self.splitter.setStretchFactor(0, 1)  # plot side expands
        self.splitter.setStretchFactor(1, 0)  # controls side stays fixed
        self.scanner.pattern = (pattern or self.SCAN_PATTERN)()
        self.scanner.pattern.polargraph = self.polargraph.device
        configdir = configdir or f'~/.{type(self).__name__}'
        self.config = Configure(configdir=configdir)
        self.restoreSettings()
        self._configurePlot()
        self._connectSignals()

    @classmethod
    def _configurePyqtgraph(cls) -> None:
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        logger.debug(f'Closing: {event.type()}')
        if self.scanner.pattern.scanning():
            self.scanner.pattern.interrupt()
            event.ignore()
            QtCore.QTimer.singleShot(100, self.close)
            return
        self.saveSettings()
        self.polargraph.device.close()
        super().closeEvent(event)

    def showStatus(self, message: str) -> None:
        '''Display a message on the status bar.'''
        self.statusBar().showMessage(message)

    def _connectSignals(self) -> None:
        self.scan.clicked.connect(self.toggleScan)
        self.polargraph.propertyChanged.connect(self.updatePlot)
        self.scanner.patternChanged.connect(self.updatePlot)
        self.scanner.pattern.dataReady.connect(self._onDataReady)
        self.home.clicked.connect(
            lambda: self._startMove(self.scanner.pattern.home))
        self.center.clicked.connect(
            lambda: self._startMove(self.scanner.pattern.center))
        self.actionSaveSettings.triggered.connect(self.saveSettings)
        self.actionRestoreSettings.triggered.connect(self.restoreSettings)

    def _configurePlot(self) -> None:
        self.plot = pg.PlotItem()
        self.graphicsView.setCentralItem(self.plot)
        self.plot.invertY(True)
        self.plot.setAspectLocked(ratio=1.)
        self.plot.showGrid(True, True, 0.2)

        pen = pg.mkPen('r', style=QtCore.Qt.PenStyle.DotLine)
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

    @QtCore.Slot(object)
    def _onDataReady(self, pos: np.ndarray) -> None:
        self._latestPosition = pos
        self.dataReady.emit({'x': float(pos[0]), 'y': float(pos[1])})

    @QtCore.Slot()
    def _updateBelt(self) -> None:
        if self._latestPosition is not None:
            self.plotBelt(self._latestPosition)
            self._latestPosition = None

    @QtCore.Slot()
    def updatePlot(self) -> None:
        self.plotTrajectory()
        self.plotBelt()

    @QtCore.Slot()
    def plotTrajectory(self) -> None:
        x, y = self.scanner.pattern.trajectory()
        self.trajectoryPlot.setData(x, y)

    @QtCore.Slot()
    @QtCore.Slot(object)
    def plotBelt(self, data: np.ndarray | None = None) -> None:
        p = self.polargraph.device
        if data is not None:
            xp, yp = data[0], data[1]
        else:
            xp, yp, _ = p.position
        x = [-p.ell / 2., xp, p.ell / 2]
        y = [0, yp, 0]
        self.beltPlot.setData(x, y)

    def plotData(self, x: npt.ArrayLike, y: npt.ArrayLike,
                 hue: npt.ArrayLike) -> None:
        '''Add scatter points to the data plot.

        Parameters
        ----------
        x : array-like
            Horizontal coordinates [m].
        y : array-like
            Vertical coordinates [m].
        hue : array-like
            Color values in ``[0, 1]`` (HSV hue).
        '''
        x = np.atleast_1d(x)
        y = np.atleast_1d(y)
        brush = [pg.hsvColor(h) for h in np.atleast_1d(hue)]
        self.dataPlot.addPoints(x, y, brush=brush)

    @QtCore.Slot()
    def toggleScan(self) -> None:
        if not self.scanner.pattern.scanning():
            self.scanStarted()
        else:
            self.scanAborted()

    def _startMove(self, fn: callable,
                   on_finished: callable | None = None) -> None:
        '''Run fn on the main thread with UI locked and belt timer active.

        Serial I/O via QSerialPort must stay on the thread that opened the
        port (the main thread).  processEvents() calls inside the scan loop
        keep the UI responsive while the blocking serial calls execute.
        '''
        for name in self._SCAN_LOCKED:
            getattr(self, name).setEnabled(False)
        self._beltTimer.start()
        fn()
        (on_finished or self._moveFinished)()

    @QtCore.Slot()
    def _moveFinished(self) -> None:
        self._beltTimer.stop()
        for name in self._SCAN_LOCKED:
            getattr(self, name).setEnabled(True)
        self.plotBelt()

    @QtCore.Slot()
    def scanStarted(self) -> None:
        self.showStatus('Scanning...')
        self.scan.setText('Stop')
        self._startMove(self.scanner.pattern.scan,
                        on_finished=self.scanFinished)

    @QtCore.Slot()
    def scanAborted(self) -> None:
        self.showStatus('Aborting scan')
        self.scanner.pattern.interrupt()
        self.scan.setText('Stopping')
        self.scan.setEnabled(False)

    @QtCore.Slot()
    def scanFinished(self) -> None:
        self._beltTimer.stop()
        self.scan.setText('Scan')
        self.scan.setEnabled(True)
        for name in self._SCAN_LOCKED:
            getattr(self, name).setEnabled(True)
        self.plotBelt()
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

        Accepts the following command-line flags:

        ``-f`` / ``--fake``
            Force use of the fake instrument.
        ``-r`` / ``--raster``
            Use :class:`~QPolargraph.RasterScan.RasterScan`.
        ``-p`` / ``--polar``
            Use :class:`~QPolargraph.PolarScan.PolarScan` (default).
        ``-t`` / ``--tarzan``
            Use :class:`~QPolargraph.TarzanScan.TarzanScan`.
        '''
        import sys
        import argparse
        parser = argparse.ArgumentParser(description=cls.__name__)
        parser.add_argument('-f', '--fake', action='store_true',
                            help='use fake instrument')
        group = parser.add_mutually_exclusive_group()
        group.add_argument('-r', '--raster', dest='pattern',
                           action='store_const', const=RasterScan,
                           help='raster scan pattern')
        group.add_argument('-p', '--polar', dest='pattern',
                           action='store_const', const=PolarScan,
                           help='polar scan pattern (default)')
        group.add_argument('-t', '--tarzan', dest='pattern',
                           action='store_const', const=TarzanScan,
                           help='Tarzan scan pattern')
        args, remaining = parser.parse_known_args()
        sys.argv = sys.argv[:1] + remaining
        pg.mkQApp(cls.__name__)
        widget = cls(fake=args.fake, pattern=args.pattern)
        widget.show()
        pg.exec()


if __name__ == '__main__':
    QScanner.example()
