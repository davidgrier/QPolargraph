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

    IDLE     : No motion in progress.
    MOVING   : Moving without collecting data (positioning or homing).
    SCANNING : Moving and collecting data.
    PAUSED   : Motion suspended; trajectory is saved for resumption.
    '''
    IDLE = auto()
    MOVING = auto()
    SCANNING = auto()
    PAUSED = auto()


class QScanPattern(QtCore.QObject):

    '''Base class for polargraph scan-trajectory patterns.

    Manages the scan geometry and drives the polargraph through a
    sequence of waypoints. Subclasses override :meth:`vertices` and
    :meth:`trajectory` to define different scan patterns.

    The motion controller is always in one of four states
    (:class:`ScanState`):

    * **IDLE** — no motion.
    * **MOVING** — positioning to the scan start or returning home;
      data are not collected.
    * **SCANNING** — actively scanning; :meth:`dataReady` is emitted
      at each position poll.
    * **PAUSED** — motion suspended; the remaining trajectory is saved
      and the polargraph holds its current position.

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
        Emitted with ``(x, y)`` [m] at every position poll during
        motion (MOVING and SCANNING states).  Connect to belt animation
        and, gated on :meth:`scanning`, to instrument data collection.
    stateChanged(ScanState)
        Emitted on every state-machine transition.  Subsumes the former
        ``moveFinished`` and ``scanFinished`` signals.
    closeRequested()
        Emitted when the state returns to IDLE after
        :meth:`interruptAndClose` was called.  Connect to the
        application window's ``close()`` slot to shut down cleanly
        after all motion stops.
    '''

    dataReady = QtCore.Signal(np.ndarray)
    stateChanged = QtCore.Signal(object)
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
        self._paused = False
        self._abandon = False
        self._closing = False
        self._paused_vertices = None
        self._pre_pause_state = None
        self._continuation = None

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
            ``(2, npts)`` array of ``(x, y)`` coordinates [m].
        '''
        return self.vertices().T

    def scanning(self) -> bool:
        '''Return ``True`` if the scanner is actively collecting data.'''
        return self._state == ScanState.SCANNING

    def moving(self) -> bool:
        '''Return ``True`` if the scanner is in motion (MOVING or SCANNING).'''
        return self._state in (ScanState.MOVING, ScanState.SCANNING)

    def active(self) -> bool:
        '''Return ``True`` if the scanner is in any non-IDLE state.'''
        return self._state != ScanState.IDLE

    def _setState(self, state: ScanState) -> None:
        if state != self._state:
            self._state = state
            self.stateChanged.emit(state)

    def _setIdle(self) -> None:
        self._setState(ScanState.IDLE)
        if self._closing:
            self._closing = False
            self.closeRequested.emit()

    def _resetTrajectory(self) -> None:
        self._paused = False
        self._abandon = False
        self._paused_vertices = None
        self._pre_pause_state = None
        self._continuation = None

    def _moveTo(self, vertices) -> str:
        '''Move through a sequence of waypoints.

        Parameters
        ----------
        vertices : list of array-like
            Sequence of ``(x, y)`` target positions [m].

        Returns
        -------
        str
            ``'complete'``, ``'paused'``, or ``'abandoned'``.
        '''
        if self.polargraph is None:
            return 'abandoned'
        for i, vertex in enumerate(vertices):
            self.polargraph.moveTo(*vertex)
            while True:
                QCoreApplication.processEvents()
                if self._abandon:
                    self.polargraph.stop()
                    self.polargraph.release()
                    self._abandon = False
                    return 'abandoned'
                if self._paused:
                    self.polargraph.stop()
                    self._paused_vertices = [vertices[j]
                                             for j in range(i, len(vertices))]
                    return 'paused'
                x, y, moving = self.polargraph.position
                self.dataReady.emit(np.array([x, y]))
                if not moving:
                    break
        self.polargraph.release()
        return 'complete'

    @QtCore.Slot()
    def home(self) -> None:
        '''Move payload to the home position.'''
        if self._state in (ScanState.MOVING, ScanState.SCANNING):
            return
        self._resetTrajectory()
        self._setState(ScanState.MOVING)
        self._moveTo([[0., self.polargraph.y0]])
        self._setIdle()

    @QtCore.Slot()
    def center(self) -> None:
        '''Move payload to the center of the scan area.'''
        if self._state in (ScanState.MOVING, ScanState.SCANNING):
            return
        self._resetTrajectory()
        self._setState(ScanState.MOVING)
        y = self.polargraph.y0 + self.dy + self.height / 2.
        self._moveTo([[self.dx, y]])
        self._setIdle()

    @QtCore.Slot()
    def scan(self) -> None:
        '''Execute a full scan, then return home.

        State transitions during a normal scan:

        ``IDLE → MOVING`` (positioning to start)
        ``→ SCANNING`` (collecting data)
        ``→ MOVING`` (returning home)
        ``→ IDLE``

        The scan may be paused at any point via :meth:`pause` and
        resumed via :meth:`resume`.  Calling :meth:`home`,
        :meth:`center`, or :meth:`abandon` while paused discards the
        saved trajectory.
        '''
        if self._state != ScanState.IDLE:
            return
        vertices = list(self.vertices())
        self._setState(ScanState.MOVING)
        result = self._moveTo([vertices[0]])
        if result == 'complete':
            self._continueScan(vertices[1:])
        elif result == 'paused':
            self._pre_pause_state = ScanState.MOVING
            self._continuation = lambda: self._continueScan(vertices[1:])
            self._setState(ScanState.PAUSED)
        else:
            self._setIdle()

    def _continueScan(self, remaining: list) -> None:
        self._setState(ScanState.SCANNING)
        result = self._moveTo(remaining)
        if result == 'complete':
            self._homeAfterScan()
        elif result == 'paused':
            self._pre_pause_state = ScanState.SCANNING
            self._continuation = self._homeAfterScan
            self._setState(ScanState.PAUSED)
        else:
            self._setIdle()

    def _homeAfterScan(self) -> None:
        self._setState(ScanState.MOVING)
        result = self._moveTo([[0., self.polargraph.y0]])
        if result == 'complete':
            self._setIdle()
        elif result == 'paused':
            self._pre_pause_state = ScanState.MOVING
            self._continuation = self._setIdle
            self._setState(ScanState.PAUSED)
        else:
            self._setIdle()

    @QtCore.Slot()
    def pause(self) -> None:
        '''Pause motion at the end of the current move.

        The polargraph stops at its current target vertex and holds
        position.  Call :meth:`resume` to continue or :meth:`abandon`
        to discard the remaining trajectory.
        '''
        if self._state in (ScanState.MOVING, ScanState.SCANNING):
            self._paused = True

    @QtCore.Slot()
    def resume(self) -> None:
        '''Resume a paused trajectory.

        Re-issues the last target vertex and continues with the
        remaining waypoints.
        '''
        if self._state != ScanState.PAUSED:
            return
        saved_vertices = self._paused_vertices or []
        saved_state = self._pre_pause_state or ScanState.MOVING
        continuation = self._continuation
        self._paused = False
        self._paused_vertices = None
        self._pre_pause_state = None
        self._continuation = None

        self._setState(saved_state)
        result = self._moveTo(saved_vertices)

        if result == 'complete':
            if continuation:
                continuation()
            else:
                self._setIdle()
        elif result == 'paused':
            self._pre_pause_state = saved_state
            self._continuation = continuation
            self._setState(ScanState.PAUSED)
        else:
            self._setIdle()

    @QtCore.Slot()
    def abandon(self) -> None:
        '''Abandon the current trajectory and return to IDLE.

        If the scanner is moving, the motors are stopped immediately.
        If paused, the saved trajectory is discarded.  The polargraph
        remains at its current position; call :meth:`home` to return
        to the home position.
        '''
        if self._state == ScanState.PAUSED:
            self._resetTrajectory()
            self._setIdle()
        elif self._state != ScanState.IDLE:
            self._abandon = True

    def interruptAndClose(self) -> None:
        '''Abandon motion and emit :attr:`closeRequested` on reaching IDLE.

        Used by the application window's ``closeEvent`` to ensure the
        polargraph stops cleanly before the application exits.
        '''
        self._closing = True
        if self._state == ScanState.PAUSED:
            self._resetTrajectory()
            self._setIdle()
        elif self._state != ScanState.IDLE:
            self._abandon = True
        else:
            self._closing = False
            self.closeRequested.emit()
