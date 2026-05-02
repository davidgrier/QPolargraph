from __future__ import annotations

from qtpy import QtCore, QtGui, QtWidgets
from QInstrument.lib.Configure import Configure
from QPolargraph.hardware.QPolargraphWidget import QPolargraphWidget
from QPolargraph.patterns.QScanPattern import QScanPattern, ScanState
from QPolargraph.patterns.QScanPatternWidget import QScanPatternWidget
from QPolargraph.patterns.PolarScan import PolarScan
from QPolargraph.patterns.RasterScan import RasterScan
from QPolargraph.patterns.TarzanScan import TarzanScan
import pyqtgraph as pg
import numpy as np
import numpy.typing as npt
import logging


logger = logging.getLogger(__name__)


class QScanner(QtWidgets.QMainWindow):

    '''Application framework for a polargraph scanner.

    Builds the UI programmatically, wires up a
    :class:`~QPolargraph.QPolargraphWidget.QPolargraphWidget` and a
    :class:`~QPolargraph.QScanPatternWidget.QScanPatternWidget`, and
    provides a live :mod:`pyqtgraph` display of the scan trajectory and
    current belt geometry. Intended to be subclassed for
    experiment-specific scanner applications.

    Class Attributes
    ----------------
    SCAN_PATTERN : type
        :class:`~QPolargraph.QScanPattern.QScanPattern` subclass to
        instantiate as the scan pattern.  Default:
        :class:`~QPolargraph.PolarScan.PolarScan`.  Subclasses override
        this to select a different scan pattern:

        .. code-block:: python

            class QMyScanner(QScanner):
                SCAN_PATTERN = RasterScan

    SCAN_WIDGET : type
        :class:`~QPolargraph.QScanPatternWidget.QScanPatternWidget`
        subclass to instantiate as the scan controls widget.  Default:
        :class:`~QPolargraph.QScanPatternWidget.QScanPatternWidget`.
        Subclasses override this to provide a custom controls widget:

        .. code-block:: python

            class QMyScanner(QScanner):
                SCAN_WIDGET = TarzanScanWidget

    Properties
    ----------
    configdir : str
        Directory for storing instrument configuration.
        Defaults to ``~/.<ClassName>`` where *ClassName* is the name of
        the concrete subclass: each subclass gets its own config directory.

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
        ``{'t': float, 'x': float, 'y': float}`` where ``t`` is a
        :func:`time.monotonic` timestamp [s] and ``x``, ``y`` are
        Cartesian coordinates [m].  Subclasses may override
        :meth:`_onDataReady` to merge in additional measurement fields
        before emitting.  Because ``_onDataReady`` runs on the GUI
        thread, instrument reads there should be fast and non-blocking;
        for tight timing call the instrument inside
        :meth:`~QPolargraph.QScanPattern.QScanPattern._onMeasure`
        instead (runs in the polargraph device thread)::

            def _onDataReady(self, pos: np.ndarray) -> None:
                self.dataReady.emit(
                    {'t': float(pos[2]), 'x': float(pos[0]),
                     'y': float(pos[1])}
                    | self.instrument.acquire())

        A sequence of emitted dicts can be collected directly into a
        :class:`pandas.DataFrame`::

            rows = []
            scanner.dataReady.connect(rows.append)
            # after scan:
            df = pd.DataFrame(rows)
    '''

    dataReady = QtCore.Signal(dict)
    _toggle = QtCore.Signal()
    _interruptClose = QtCore.Signal()

    SCAN_PATTERN = PolarScan
    SCAN_WIDGET = QScanPatternWidget

    def __init__(self, *args,
                 configdir: str | None = None,
                 fake: bool = False,
                 pattern: type | None = None,
                 **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._belt_pos = None
        self.setupPolargraph(fake)
        self.setupScanner(pattern)
        self.configure(configdir)
        self.setupUi()
        self.connectSignals()
        self.updatePlot()

    def setupPolargraph(self, fake: bool) -> None:
        device = QPolargraphWidget._fakeCls()() if fake else None
        self.polargraph = QPolargraphWidget(device=device)

    def setupScanner(self, pattern: type | None) -> None:
        pg = self.polargraph.device
        scan_pattern = (pattern or self.SCAN_PATTERN)(polargraph=pg)
        self.scanner = self.SCAN_WIDGET(pattern=scan_pattern)

    def configure(self, configdir: str | None) -> None:
        configdir = configdir or f'~/.{type(self).__name__}'
        self.config = Configure(configdir=configdir)
        self.restoreSettings()

    def setupUi(self) -> None:
        self.setWindowTitle(type(self).__name__)
        geom = QtWidgets.QApplication.primaryScreen().availableGeometry()
        self.resize(geom.width() * 2 // 3, geom.height() * 2 // 3)

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        main = QtWidgets.QHBoxLayout(central)

        # Left: buttons + plot
        scanWidget = QtWidgets.QWidget()
        scanLayout = QtWidgets.QVBoxLayout(scanWidget)
        scanLayout.setSpacing(1)
        scanLayout.setContentsMargins(2, 1, 2, 1)

        buttons = QtWidgets.QWidget()
        buttonLayout = QtWidgets.QHBoxLayout(buttons)
        self.home = QtWidgets.QPushButton('Home')
        self.center = QtWidgets.QPushButton('Center')
        self.scan = QtWidgets.QPushButton('Scan')
        buttonLayout.addWidget(self.home)
        buttonLayout.addWidget(self.center)
        buttonLayout.addWidget(self.scan)

        self.graphicsView = pg.GraphicsView()
        self.graphicsView.setBackground('w')

        scanLayout.addWidget(buttons, stretch=0)
        scanLayout.addWidget(self.graphicsView, stretch=1)
        main.addWidget(scanWidget, stretch=1)

        # Right: instrument controls
        controls = QtWidgets.QWidget()
        controlsLayout = QtWidgets.QVBoxLayout(controls)
        controlsLayout.setSpacing(1)
        controlsLayout.setContentsMargins(2, 1, 2, 1)

        polargraphBox = QtWidgets.QGroupBox('Polargraph')
        polargraphLayout = QtWidgets.QVBoxLayout(polargraphBox)
        polargraphLayout.setSpacing(1)
        polargraphLayout.setContentsMargins(2, 1, 2, 1)
        polargraphLayout.addWidget(self.polargraph)
        controlsLayout.addWidget(polargraphBox, stretch=0)

        scannerBox = QtWidgets.QGroupBox('Scan setup')
        scannerLayout = QtWidgets.QVBoxLayout(scannerBox)
        scannerLayout.setSpacing(1)
        scannerLayout.setContentsMargins(2, 1, 2, 1)
        scannerLayout.addWidget(self.scanner)
        controlsLayout.addWidget(scannerBox, stretch=0)
        controlsLayout.addStretch(1)

        main.addWidget(controls, stretch=0)

        # Plot items
        self.plot = pg.PlotItem()
        self.graphicsView.setCentralItem(self.plot)
        self.plot.invertY(True)
        self.plot.setAspectLocked(ratio=1.)
        self.plot.showGrid(True, True, 0.2)
        for name in ('left', 'bottom'):
            axis = self.plot.getAxis(name)
            axis.setPen('k')
            axis.setTextPen('k')

        pen = pg.mkPen('r', style=QtCore.Qt.PenStyle.DotLine)
        self.trajectoryPlot = pg.PlotDataItem(pen=pen)
        self.plot.addItem(self.trajectoryPlot)

        pen = pg.mkPen('k', width=3)
        brush = pg.mkBrush('y')
        self.beltPlot = pg.PlotDataItem(pen=pen, symbol='o',
                                        symbolPen=pen, symbolBrush=brush)
        self.plot.addItem(self.beltPlot)

        self.dataPlot = pg.ScatterPlotItem(pen=None)
        self.plot.addItem(self.dataPlot)

        # Menu bar
        fileMenu = self.menuBar().addMenu('File')
        self.actionSaveSettings = fileMenu.addAction('Save Settings')
        self.actionRestoreSettings = fileMenu.addAction('Restore Settings')
        fileMenu.addSeparator()
        self.actionSaveData = fileMenu.addAction('Save Data')
        self.actionSaveDataAs = fileMenu.addAction('Save Data As ...')
        self.actionLoadData = fileMenu.addAction('Load Data ...')
        fileMenu.addSeparator()
        self.actionQuit = fileMenu.addAction('Quit')
        self.actionQuit.triggered.connect(self.close)

        self.statusBar()

    def connectSignals(self) -> None:
        self.polargraph.propertyChanged.connect(self.updatePlot)
        self.scanner.patternChanged.connect(self.updatePlot)
        self.scanner.pattern.dataReady.connect(self.plotBelt)
        self.scanner.pattern.dataReady.connect(self._onDataReady)
        self.scanner.pattern.stateChanged.connect(self._onStateChanged)
        self.scanner.pattern.closeRequested.connect(self._onCloseRequested)
        self._toggle.connect(self.scanner.pattern.toggle)
        self._interruptClose.connect(self.scanner.pattern.interruptAndClose)

        self.scan.clicked.connect(self.toggleScan)
        self.center.clicked.connect(self.scanner.pattern.center)
        self.home.clicked.connect(self.scanner.pattern.home)

        QtCore.QTimer.singleShot(0, self._syncPatternThread)

        self.actionSaveSettings.triggered.connect(self.saveSettings)
        self.actionRestoreSettings.triggered.connect(self.restoreSettings)

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
            xp, yp = float(data[0]), float(data[1])
            self._belt_pos = (xp, yp)
        elif self._belt_pos is not None:
            xp, yp = self._belt_pos
        else:
            xp, yp = 0., p.y0
        x = [-p.ell / 2., xp, p.ell / 2.]
        y = [0., yp, 0.]
        self.beltPlot.setData(x, y)

    def _lockedWidgets(self) -> list:
        '''Widgets disabled during MOVING and SCANNING states.

        Subclasses that add controls which should also be locked during a
        scan can extend this list::

            def _lockedWidgets(self):
                return super()._lockedWidgets() + [self.my_widget]
        '''
        return [self.center, self.home, self.polargraph, self.scanner]

    def _onStateChanged(self, state: ScanState) -> None:
        locked = state in (ScanState.MOVING, ScanState.SCANNING)
        for widget in self._lockedWidgets():
            widget.setEnabled(not locked)
        if state == ScanState.IDLE:
            self.scan.setText('Scan')
            self.scan.setEnabled(True)
            self.showStatus('Scan complete')
        elif state == ScanState.PAUSED:
            self.scan.setText('Resume')
            self.scan.setEnabled(True)
            self.showStatus('Scan paused')
        else:
            self.scan.setText('Pause')
            self.scan.setEnabled(state == ScanState.SCANNING)

    @QtCore.Slot()
    def toggleScan(self) -> None:
        '''Emit the toggle signal to start, pause, or resume the scan.

        Routes through ``_toggle`` so the call is delivered as a
        ``QueuedConnection`` when the scan pattern lives in a worker
        thread (real hardware), or as a ``DirectConnection`` in tests.
        '''
        self._toggle.emit()

    def _syncPatternThread(self) -> None:
        '''Move the scan pattern to the polargraph device thread.

        Called once, deferred, after construction so that
        ``QPolargraphWidget._firstShow`` has had time to run and move
        the serial device to its worker thread.  No-ops for fake
        instruments (which stay on the main thread).  Retries every
        50 ms until the device has actually moved.
        '''
        from QInstrument.lib.QSerialInstrument import QSerialInstrument
        if not isinstance(self.polargraph.device, QSerialInstrument):
            return
        device_thread = self.polargraph.device.thread()
        if device_thread is QtCore.QThread.currentThread():
            QtCore.QTimer.singleShot(50, self._syncPatternThread)
            return
        if self.scanner.pattern.thread() is not device_thread:
            self.scanner.pattern.moveToThread(device_thread)

    @QtCore.Slot(object)
    def _onDataReady(self, pos: np.ndarray) -> None:
        if self.scanner.pattern.scanning():
            self.dataReady.emit({'t': float(pos[2]),
                                 'x': float(pos[0]),
                                 'y': float(pos[1])})

    def plotData(self, x: npt.ArrayLike, y: npt.ArrayLike,
                 hue: npt.ArrayLike,
                 saturation: npt.ArrayLike = 1.0) -> None:
        '''Add scatter points to the data plot.

        Parameters
        ----------
        x : array-like
            Horizontal coordinates [m].
        y : array-like
            Vertical coordinates [m].
        hue : array-like
            Color values in ``[0, 1]`` (HSV hue).
        saturation : array-like, optional
            Saturation values in ``[0, 1]`` (HSV saturation).
            Default: 1.0 (fully saturated).  Low saturation appears
            white, high saturation gives the pure hue color.
        '''
        x = np.atleast_1d(x)
        y = np.atleast_1d(y)
        hue = np.atleast_1d(hue)
        saturation = np.broadcast_to(np.atleast_1d(saturation), hue.shape)
        brush = [pg.hsvColor(h, sat=s) for h, s in zip(hue, saturation)]
        self.dataPlot.addPoints(x, y, brush=brush)

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

    def showStatus(self, message: str) -> None:
        '''Display a message on the status bar.'''
        self.statusBar().showMessage(message)

    def _onCloseRequested(self) -> None:
        self.close()

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        logger.debug(f'Closing: {event.type()}')
        if self.scanner.pattern.active():
            self._interruptClose.emit()
            event.ignore()
            return
        self.saveSettings()
        self.polargraph.close()
        super().closeEvent(event)

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
