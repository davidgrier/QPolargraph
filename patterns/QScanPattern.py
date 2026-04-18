from __future__ import annotations
from enum import auto, Enum
from typing import TYPE_CHECKING
from qtpy import QtCore
from qtpy.QtCore import QCoreApplication
import numpy as np
import logging

if TYPE_CHECKING:
    from QPolargraph.hardware.Polargraph import Polargraph


logger = logging.getLogger(__name__)


class ScanState(Enum):
    '''State of the scan pattern motion controller.

    IDLE    : No motion in progress; instruments are inactive.
    MOVING  : Moving but not collecting data (initial positioning or homing).
    SCANNING: Moving and collecting data.
    '''
    IDLE = auto()
    MOVING = auto()
    SCANNING = auto()


class QScanPattern(QtCore.QObject):

    '''Base class for polargraph scan-trajectory patterns.

    Manages the scan geometry and drives the polargraph through a
    sequence of waypoints. Subclasses override :meth:`vertices` and
    :meth:`trajectory` to define different scan patterns.

    The motion controller is always in one of three states
    (:class:`ScanState`):

    * **IDLE** — no motion; :meth:`scanning` and :meth:`moving` both
      return ``False``.
    * **MOVING** — positioning to the scan start or returning home;
      :meth:`moving` returns ``True``, :meth:`scanning` returns ``False``.
    * **SCANNING** — actively scanning and emitting data; both
      :meth:`moving` and :meth:`scanning` return ``True``.

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
        Emitted when a full :meth:`scan` completes (including the return
        to home, if applicable).
    closeRequested()
        Emitted when the state returns to IDLE after
        :meth:`interruptAndClose` was called.  Connect to the
        application window's ``close()`` slot with a
        ``QueuedConnection`` to shut down cleanly after all motion stops.
    '''

    dataReady = QtCore.Signal(np.ndarray)
    moveFinished = QtCore.Signal()
    scanFinished = QtCore.Signal()
    closeRequested = QtCore.Signal()

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
        self._state = ScanState.IDLE
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

    @property
    def rect(self) -> list:
        '''Bounding rectangle ``[x1, y1, x2, y2]`` of the scan area [m].'''
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
        x1, y1, x2, y2 = self.rect
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

    def scanning(self) -> bool:
        '''Return ``True`` if the scanner is actively collecting data.'''
        return self._state == ScanState.SCANNING

    def moving(self) -> bool:
        '''Return ``True`` if the scanner is in motion (MOVING or SCANNING).'''
        return self._state != ScanState.IDLE

    def _setIdle(self) -> None:
        '''Transition to IDLE and emit closeRequested if a close is pending.'''
        self._state = ScanState.IDLE
        if self._closing:
            self._closing = False
            self.closeRequested.emit()

    @QtCore.Slot()
    def home(self) -> None:
        '''Move payload to the home position ``(0, y0)``.'''
        self._state = ScanState.MOVING
        self.moveTo([[0., self.polargraph.y0]])
        self._setIdle()

    @QtCore.Slot()
    def center(self) -> None:
        '''Move payload to the center of the scan area.'''
        self._state = ScanState.MOVING
        y = self.polargraph.y0 + self.dy + self.height / 2.
        self.moveTo([[self.dx, y]])
        self._setIdle()

    @QtCore.Slot()
    def scan(self) -> None:
        '''Execute a full scan, then return to home.

        State transitions during a normal scan:

        ``IDLE → MOVING`` (positioning to start)
        ``→ SCANNING`` (collecting data)
        ``→ MOVING`` (returning home via :meth:`home`)
        ``→ IDLE``

        After a normal Stop, the scanner returns home before reaching IDLE.
        After :meth:`interruptAndClose`, the home move is skipped and
        :attr:`closeRequested` is emitted on reaching IDLE.
        '''
        if self._state != ScanState.IDLE:
            self.interrupt()
            return
        vertices = self.vertices()
        self._state = ScanState.MOVING
        if self.moveTo([vertices[0, :]]):
            self._state = ScanState.SCANNING
            interrupted = not self.moveTo(vertices[1:, :])
            self._state = ScanState.MOVING
            if not (interrupted and self._closing):
                self.home()          # home() calls _setIdle()
                self.scanFinished.emit()
                return
        self._setIdle()
        self.scanFinished.emit()

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
                x, y, moving = self.polargraph.position
                if not moving:
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
        '''Request that the current motion be aborted.

        The scanner will stop at its current position and then return
        to the home position.  To stop without going home (e.g. when
        the application window is closing), use :meth:`interruptAndClose`.
        '''
        self._interrupt = True

    def interruptAndClose(self) -> None:
        '''Interrupt motion and signal that the application is closing.

        Like :meth:`interrupt`, but sets an internal flag so that
        :meth:`scan` skips the return-home move and instead emits
        :attr:`closeRequested` when the state returns to IDLE.
        '''
        self._closing = True
        self._interrupt = True
