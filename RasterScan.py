from PyQt5.QtCore import (QObject, pyqtProperty, pyqtSlot, pyqtSignal)
import numpy as np
import logging


logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


class RasterScan(QObject):

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
        self._interrupt = False

    def rect(self):
        x1 = self.dx - self.width/2.
        y1 = self.y0 + self.dy
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
        x = np.arange(x1, x2, self.step*1e-3)
        y = np.full_like(x, y1)
        y[1::2] = y2
        return np.vstack([x, y]).T

    def trajectory(self):
        '''Coordinates along the scan path

        Returns
        -------
        xy: numpy.ndarray
            (2, npts) array of x-y coordinates along scan path,
            suitable for plotting
        '''
        return self.vertices().T

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
        if self._moving:
            self._interrupt = True
        else:
            self.moveTo(self.vertices())
            self.scanFinished.emit()

    @pyqtSlot(list)
    def moveTo(self, vertices):
        '''Move polargraph to vertices'''
        if self.polargraph is None:
            return
        if self._moving or self._interrupt:
            self._interrupt = False
            return
        self._moving = True
        for vertex in vertices:
            logger.debug(f'Moving to: {vertex}')
            self.polargraph.moveTo(*vertex)
            while(True):
                x, y, running = self.polargraph.position
                if (not running) or self._interrupt:
                    break
                self.process(np.array([x, y]))
            else:
                logger.debug(f'Reached goal: {vertex}')
                self.processStep()
            if self._interrupt:
                break
        self.polargraph.release()
        self._moving = False
        self.moveFinished.emit()

    def process(self, pos):
        self.dataReady.emit(pos)

    def processStep(self):
        pass

    @pyqtSlot()
    def interrupt(self):
        self._interrupt = True
