import numpy as np
from PyQt5.QtCore import (QObject, pyqtProperty, pyqtSignal, pyqtSlot)
import logging


logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


class ScanPattern(QObject):

    def Property(pname):
        key = f'_{pname}'

        def getter(self):
            value = getattr(self, key)
            logger.debug(f'Getting: {key} {value}')
            return value

        def setter(self, value):
            logger.debug(f'Setting: {key} {value}')
            setattr(self, key, value)
        return pyqtProperty(float, getter, setter)

    width = Property('width')
    height = Property('height')
    dx = Property('dx')
    dy = Property('dy')
    step = Property('step')
    y0 = Property('y0')

    dataReady = pyqtSignal(np.ndarray)
    moveFinished = pyqtSignal()
    scanFinished = pyqtSignal()

    def __init__(self, *args,
                 width=0.6,
                 height=0.6,
                 dx=0.,
                 dy=0.1,
                 step=5,
                 y0=0.1,
                 polargraph=None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.width = width
        self.height = height
        self.dx = dx
        self.dy = dy
        self.step = step
        self.y0 = y0
        self.polargraph = polargraph
        self._moving = False
        self._scanning = False
        self._interrupt = False

    def rect(self):
        x1 = self.dx - self.width/2.
        y1 = self.y0 + self.dy
        x2 = x1 + self.width
        y2 = y1 + self.height
        return [x1, y1, x2, y2]

    def vertices(self):
        '''Returns array of target positions for polargraph motions'''
        x1, y1, x2, y2 = self.rect()
        return np.array([[x1, y1], [x2, y1], [x2, y2], [x1, y2], [x1, y1]])

    def trajectory(self):
        '''Returns array of points along the planned trajectory for plotting'''
        return self.vertices()

    def isOpen(self):
        '''Method required for QInstrumentWidget interface'''
        return True

    @pyqtSlot()
    def home(self):
        '''Move payload to home position: (0, y0)'''
        self.moveTo([[0., self.y0]])

    @pyqtSlot()
    def center(self):
        '''Move payload to center of scan range'''
        y = self.y0 + self.dy + self.height/2.
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
