import numpy as np
from PyQt5.QtCore import (QObject, pyqtProperty, pyqtSignal, pyqtSlot)
import logging


logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


class PolarScan(QObject):

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

    def radii(self):
        L = self.polargraph.ell/2
        x1, y1, x2, y2 = self.rect()
        rmin = np.hypot(x1 + L, y1)
        rmax = np.hypot(x2 + L, y2)
        return np.arange(rmin, rmax, self.step*1e-3)

    def intercepts(self, r):
        p = -self.polargraph.ell/2
        x1, y1, x2, y2 = self.rect()
        x1 -= p
        x2 -= p

        if (r < np.hypot(x2, y1)):
            r1 = [p + np.sqrt(r**2 - y1**2), y1]
        else:
            r1 = [p + x2, np.sqrt(r**2 - x2**2)]
        if (r < np.hypot(x1, y2)):
            r2 = [p + x1, np.sqrt(r**2 - x1**2)]
        else:
            r2 = [p + np.sqrt(r**2 - y2**2), y2]

        return [r1, r2]

    def vertices(self):
        xy = np.array([])
        for n, r in enumerate(self.radii()):
            p1, p2 = self.intercepts(r)
            if (n % 2) == 0:
                p1, p2 = p2, p1
            xy = np.append(xy, [p1, p2])
        return xy.reshape(-1, 2)

    def trajectory(self):
        L = self.polargraph.ell
        x = np.array([])
        y = np.array([])
        points = self.vertices().reshape(-1, 4)
        for n, r in enumerate(self.radii()):
            x1, y1, x2, y2 = points[n]
            s1 = np.sqrt(r**2 - 2.*L*x1)
            s2 = np.sqrt(r**2 - 2.*L*x2)
            s = np.linspace(s1, s2)
            thisx = (r**2 - s**2)/(2.*L)
            x = np.append(x, thisx)
            y = np.append(y, np.sqrt(r**2 - (L/2. + thisx)**2))
        return [x, y]

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
            self.moveTo([vertices[0, :]])
            self._scanning = True
            self.moveTo(vertices[1:, :])
            self._scanning = False
            self._interrupt = False
            self.home()
            self.scanFinished.emit()
        else:
            self._interrupt = True

    def scanning(self):
        return self._scanning

    @pyqtSlot(list)
    def moveTo(self, vertices):
        '''Move polargraph to vertices'''
        if self.polargraph is None:
            return
        if self._interrupt:
            self._interrupt = False
            return
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
        self.polargraph.release()
        self.moveFinished.emit()

    @pyqtSlot()
    def interrupt(self):
        self._interrupt = True
