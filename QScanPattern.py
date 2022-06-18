import numpy as np
from PyQt5.QtCore import (QObject, pyqtProperty, pyqtSignal, pyqtSlot)
import logging


logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


class Property(pyqtProperty):

    def __init__(self, value, name=''):
        super().__init__(type(value), self.getter, self.setter)
        self.value = value
        self.name = name

    def getter(self, inst=None):
        logger.debug(f'Getting {self.name}')
        return self.value

    def setter(self, inst=None, value=None):
        logger.debug(f'Setting {self.name}: {value}')
        self.value = value


class PropertyMeta(type(QObject)):
    def __new__(mcs, name, bases, attrs):
        for key in list(attrs.keys()):
            attr = attrs[key]
            if not isinstance(attr, Property):
                continue
            value = attr.value
            attrs[key] = Property(value, key)
        return super().__new__(mcs, name, bases, attrs)


class QScanPattern(QObject, metaclass=PropertyMeta):

    width = Property(0.6)
    height = Property(0.6)
    dx = Property(0.)
    dy = Property(0.)
    step = Property(5.)

    dataReady = pyqtSignal(np.ndarray)
    moveFinished = pyqtSignal()
    scanFinished = pyqtSignal()

    def __init__(self, *args,
                 width=0.6,
                 height=0.6,
                 dx=0.,
                 dy=0.1,
                 step=5,
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

    def rect(self):
        x1 = self.dx - self.width/2.
        y1 = self.polargraph.y0 + self.dy
        x2 = x1 + self.width
        y2 = y1 + self.height
        return [x1, y1, x2, y2]

    def vertices(self):
        '''Vertices of the scan trajectory

        Returns
        -------
        xy: numpy.ndarray
            (nvertices, 2) array of vertices of scan trajectory
        '''
        x1, y1, x2, y2 = self.rect()
        return np.array([[x1, y1], [x2, y1], [x2, y2], [x1, y2], [x1, y1]])

    def trajectory(self):
        '''Coordinates along the scan path

        Returns
        -------
        xy: numpy.ndarray
            (2, npts) array of x-y coordinates along scan path,
            suitable for plotting
        '''
        return self.vertices()

    def isOpen(self):
        '''Method required for QInstrumentWidget interface'''
        return True

    @pyqtSlot()
    def home(self):
        '''Move payload to home position: (0, y0)'''
        self.moveTo([[0., self.polargraph.y0]])

    @pyqtSlot()
    def center(self):
        '''Move payload to center of scan range'''
        y = self.polargraph.y0 + self.dy + self.height/2.
        self.moveTo([[self.dx, y]])

    @pyqtSlot()
    def scan(self):
        '''Perform scan'''
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

    def scanning(self):
        return self._scanning

    @pyqtSlot(list)
    def moveTo(self, vertices):
        '''Move polargraph to vertices'''
        if self.polargraph is None:
            return False
        for vertex in vertices:
            logger.debug(f'Moving to: {vertex}')
            self.polargraph.moveTo(*vertex)
            while(True):
                if self._interrupt:
                    self.polargraph.stop()
                x, y, self._moving = self.polargraph.position
                if not self._moving:
                    break
                self.dataReady.emit(np.array([x, y]))
            else:
                logger.debug(f'Reached goal: {vertex}')
            if self._interrupt:
                break
        success = not self._interrupt
        self._interrupt = False
        self.polargraph.release()
        self.moveFinished.emit()
        return success

    @pyqtSlot()
    def interrupt(self):
        self._interrupt = True
