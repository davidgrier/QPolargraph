from __future__ import annotations
from typing import TYPE_CHECKING
from qtpy import QtCore
from qtpy.QtCore import QCoreApplication
import numpy as np
import logging

if TYPE_CHECKING:
    from QPolargraph.hardware.Polargraph import Polargraph


logger = logging.getLogger(__name__)


class QScanPattern(QtCore.QObject):

    '''Base class for polargraph scan-trajectory patterns.

    Manages the scan geometry and drives the polargraph through a
    sequence of waypoints. Subclasses override :meth:`vertices` and
    :meth:`trajectory` to define different scan patterns.

    Properties
    ----------
    width : float
        Horizontal extent of the scan area [m]. Default: 0.6.
    height : float
        Vertical extent of the scan area [m]. Default: 0.6.
    dx : float
        Horizontal offset of the scan area center from the polargraph
        centerline [m]. Default: 0.
    dy : float
        Vertical offset of the scan area top edge below the home
        position [m]. Default: 0.1.
    step : float
        Spacing between scan lines [mm]. Default: 5.

    Signals
    -------
    dataReady(numpy.ndarray)
        Emitted with the current ``(x, y)`` position during a move.
    moveFinished()
        Emitted when a :meth:`moveTo` call completes.
    scanFinished()
        Emitted when a full :meth:`scan` completes.
    '''

    dataReady = QtCore.Signal(np.ndarray)
    moveFinished = QtCore.Signal()
    scanFinished = QtCore.Signal()

    def __init__(self, *args,
                 width: float = 0.6,
                 height: float = 0.6,
                 dx: float = 0.,
                 dy: float = 0.1,
                 step: float = 5,
                 polargraph: Polargraph | None = None,
                 **kwargs):
        super().__init__(**kwargs)
        self._width = width
        self._height = height
        self._dx = dx
        self._dy = dy
        self._step = step
        self.polargraph = polargraph
        self._moving = False
        self._scanning = False
        self._interrupt = False
        self._closing = False

    @property
    def width(self) -> float:
        '''Horizontal extent of the scan area [m].'''
        return self._width

    @width.setter
    def width(self, value: float) -> None:
        self._width = float(value)

    @property
    def height(self) -> float:
        '''Vertical extent of the scan area [m].'''
        return self._height

    @height.setter
    def height(self, value: float) -> None:
        self._height = float(value)

    @property
    def dx(self) -> float:
        '''Horizontal offset of scan center from polargraph centerline [m].'''
        return self._dx

    @dx.setter
    def dx(self, value: float) -> None:
        self._dx = float(value)

    @property
    def dy(self) -> float:
        '''Vertical offset of scan top edge below home position [m].'''
        return self._dy

    @dy.setter
    def dy(self, value: float) -> None:
        self._dy = float(value)

    @property
    def step(self) -> float:
        '''Spacing between scan lines [mm].'''
        return self._step

    @step.setter
    def step(self, value: float) -> None:
        self._step = float(value)

    def isOpen(self) -> bool:
        '''Return ``True`` — scan patterns are always available.'''
        return True

    def rect(self) -> list:
        '''Return the bounding rectangle ``[x1, y1, x2, y2]`` [m].'''
        x1 = self.dx - self.width / 2.
        y1 = self.polargraph.y0 + self.dy
        x2 = x1 + self.width
        y2 = y1 + self.height
        return [x1, y1, x2, y2]

    def vertices(self) -> np.ndarray:
        '''Vertices of the scan trajectory.

        Returns
        -------
        numpy.ndarray
            ``(nvertices, 2)`` array of ``(x, y)`` waypoints [m].
        '''
        x1, y1, x2, y2 = self.rect()
        return np.array([[x1, y1], [x2, y1], [x2, y2], [x1, y2], [x1, y1]])

    def trajectory(self) -> np.ndarray:
        '''Coordinates along the scan path for display.

        Returns
        -------
        numpy.ndarray
            ``(2, npts)`` array of ``(x, y)`` coordinates [m],
            suitable for plotting.
        '''
        return self.vertices().T

    @QtCore.Slot()
    def home(self) -> None:
        '''Move payload to the home position ``(0, y0)``.'''
        self.moveTo([[0., self.polargraph.y0]])

    @QtCore.Slot()
    def center(self) -> None:
        '''Move payload to the center of the scan area.'''
        y = self.polargraph.y0 + self.dy + self.height / 2.
        self.moveTo([[self.dx, y]])

    @QtCore.Slot()
    def scan(self) -> None:
        '''Execute a full scan, then return to home.

        Returns home after completion or after a normal stop.  Skips home
        only when interrupted by a window-close request
        (see :meth:`interruptAndClose`).
        '''
        if not self._moving:
            vertices = self.vertices()
            self._scanning = True
            if self.moveTo([vertices[0, :]]):
                interrupted = not self.moveTo(vertices[1:, :])
                if not (interrupted and self._closing):
                    self.home()
            self._scanning = False
            self._closing = False
            self.scanFinished.emit()
        else:
            self.interrupt()

    def scanning(self) -> bool:
        '''Return ``True`` if a scan is in progress.'''
        return self._scanning

    @QtCore.Slot(list)
    def moveTo(self, vertices) -> bool:
        '''Move the polargraph through a sequence of waypoints.

        Parameters
        ----------
        vertices : list of array-like
            Sequence of ``(x, y)`` target positions [m].

        Returns
        -------
        bool
            ``True`` if all waypoints were reached; ``False`` if
            interrupted.
        '''
        if self.polargraph is None:
            return False
        for vertex in vertices:
            logger.debug(f'Moving to: {vertex}')
            self.polargraph.moveTo(*vertex)
            while True:
                QCoreApplication.processEvents()
                if self._interrupt:
                    self.polargraph.stop()
                x, y, self._moving = self.polargraph.position
                if not self._moving:
                    break
                self.dataReady.emit(np.array([x, y]))
            logger.debug(f'Reached goal: {vertex}')
            if self._interrupt:
                break
        success = not self._interrupt
        self._interrupt = False
        self.polargraph.release()
        self.moveFinished.emit()
        return success

    @QtCore.Slot()
    def interrupt(self) -> None:
        '''Request that the current scan or move be aborted.

        After stopping, the scanner returns to the home position.
        To stop without going home (e.g. on application close),
        use :meth:`interruptAndClose` instead.
        '''
        self._interrupt = True

    def interruptAndClose(self) -> None:
        '''Interrupt the current scan without returning home.

        Used by the application close handler to stop motion cleanly
        without blocking on a home move before shutdown.
        '''
        self._closing = True
        self._interrupt = True
