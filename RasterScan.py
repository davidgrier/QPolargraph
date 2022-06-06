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

    dataReady = pyqtSignal(list)
    moveFinished = pyqtSignal()

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

    def trajectory(self):
        x1 = self.dx - self.width/2.
        y1 = self.y0 + self.dy
        x2 = x1 + self.width
        y2 = y1 + self.height

        x = np.arange(x1, x2, self.step*1e-3)
        y = np.full_like(x, y1)
        y[1::2] = y2
        return x, y

    def isOpen(self):
        return True

    @pyqtSlot()
    def home(self):
        self.moveTo([[0., self.y0]])

    @pyqtSlot()
    def center(self):
        y = self.y0 + self.dy + self.height/2.
        self.moveTo([[self.dx, y]])

    @pyqtSlot()
    def scan(self):
        if self._moving:
            self._interrupt = True
        else:
            x, y = self.trajectory()
            self.moveTo([(xn, yn) for xn, yn in zip(x, y)])

    @pyqtSlot(list)
    def moveTo(self, trajectory):
        if self.polargraph is None:
            return
        if self._moving or self._interrupt:
            self._interrupt = False
            return
        self._moving = True
        for goal in trajectory:
            logger.debug(f'Moving to: {goal}')
            self.polargraph.moveTo(*goal)
            while(self.polargraph.running()):
                self.processMotion()
                if self._interrupt:
                    break
            self.processStep()
            if self._interrupt:
                break
        self.polargraph.release()
        self._moving = False
        self.moveFinished.emit()

    def processMotion(self):
        pos = self.polargraph.position
        self.dataReady.emit(pos)

    def processStep(self):
        pass
