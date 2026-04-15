from qtpy import QtCore
import numpy as np
import logging


logger = logging.getLogger(__name__)


class _Property(QtCore.Property):

    def __init__(self, value, name: str = ''):
        super().__init__(type(value), self.getter, self.setter)
        self.value = value
        self.name = name

    def getter(self, inst=None):
        logger.debug(f'Getting {self.name}')
        return self.value

    def setter(self, inst=None, value=None):
        logger.debug(f'Setting {self.name}: {value}')
        self.value = value


class _PropertyMeta(type(QtCore.QObject)):
    def __new__(mcs, name, bases, attrs):
        for key in list(attrs.keys()):
            attr = attrs[key]
            if not isinstance(attr, _Property):
                continue
            value = attr.value
            attrs[key] = _Property(value, key)
        return super().__new__(mcs, name, bases, attrs)


class QScanPattern(QtCore.QObject, metaclass=_PropertyMeta):

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
        Horizontal offset of the scan area centre from the polargraph
        centreline [m]. Default: 0.
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

    width = _Property(0.6)
    height = _Property(0.6)
    dx = _Property(0.)
    dy = _Property(0.)
    step = _Property(5.)

    dataReady = QtCore.Signal(np.ndarray)
    moveFinished = QtCore.Signal()
    scanFinished = QtCore.Signal()

    def __init__(self, *args,
                 width: float = 0.6,
                 height: float = 0.6,
                 dx: float = 0.,
                 dy: float = 0.1,
                 step: float = 5,
                 polargraph=None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.width = width
        self.height = height
        self.dx = dx
        self.dy = dy
        self.step = step
        self.polargraph = polargraph
        self._moving = False
        self._scanning = False
        self._interrupt = False

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
        return self.vertices()

    def isOpen(self) -> bool:
        '''Return ``True`` — satisfies the :class:`QInstrumentWidget` interface.'''
        return True

    @QtCore.Slot()
    def home(self) -> None:
        '''Move payload to the home position ``(0, y0)``.'''
        self.moveTo([[0., self.polargraph.y0]])

    @QtCore.Slot()
    def center(self) -> None:
        '''Move payload to the centre of the scan area.'''
        y = self.polargraph.y0 + self.dy + self.height / 2.
        self.moveTo([[self.dx, y]])

    @QtCore.Slot()
    def scan(self) -> None:
        '''Execute a full scan, then return to home.'''
        if not self._moving:
            vertices = self.vertices()
            if self.moveTo([vertices[0, :]]):
                self._scanning = True
                self.moveTo(vertices[1:, :])
                self._scanning = False
            self.home()
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
        '''Request that the current scan or move be aborted.'''
        self._interrupt = True
