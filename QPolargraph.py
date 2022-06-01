from QPolargraph.device.QMotors import QMotors
from PyQt5.QtCore import pyqtProperty
import numpy as np
import logging

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class QPolargraph(QMotors):

    '''
    Abstraction of a polargraph

    The polargraph consists of two stepper motors with GT2 gears
    that translate a GT2 timing belt.  The motors are controlled
    by an Arduino microcontroller that is connected to the host
    computer by USB.  This class communicates with the Arduino to
    obtain programmed motion from the motors.

    ...

    Attributes
    ----------
    pitch : float
        Separation between teeth on timing belt [mm]
        Default: 2.
    circumference : float
        Number of teeth per revolution.
        Default: 25.
    steps : float
        Number of motor steps per revolution.
        Default: 200.
    ell : float
        Separation between motors [m]
    y0 : float
        Vertical displacement of home position [m]
    y1 : float
        Vertical position of scan start [m]
    width : float
        Width of scan area [m]
    height : float
        Height of scan area [m]
    dy : float
        Vertical displacement between scan lines [m]
    ds : float
        Distance traveled per motor step [m]
    s0 : float
        Length of belt from motor to payload at home position [m]
    position : (x, y)
       Report current coordinates of payload measured in
       meters from home position.
    speed : float
       Translation speed [mm/s]

    Methods
    -------
    goto(x, y)
       Move payload to coordinates (x, y), measured in meters
       from home position.
    '''

    def __init__(self,
                 pitch=2.,           # size of one timing belt tooth [mm]
                 circumference=25.,  # belt teeth per revolution
                 steps=200.,         # motor steps per revolution
                 ell=1.,             # separation between motors [m]
                 y0=0.1,             # home position [m]
                 width=0.6,          # width of scan area [m]
                 height=0.6,         # height of scan area [m]
                 dy=0.005,           # interscanline displacement [m]
                 **kwargs):

        super().__init__(**kwargs)

        # Belt drive
        self.pitch = float(pitch)
        self.circumference = float(circumference)
        self.steps = float(steps)

        # Motor configuration
        self.ell = float(ell)
        self.y0 = float(y0)

        # Scan configuration
        self.x1 = 0.
        self.y1 = 0.
        self.width = float(width)
        self.height = float(height)
        self.dy = float(dy)
        self.busy = self.running

    @pyqtProperty(float)
    def ds(self):
        '''Distance traveled per step [m]'''
        return 1e-3 * self.pitch * self.circumference / self.steps

    @pyqtProperty(float)
    def s0(self):
        '''Distance from motor to payload at home position [m]'''
        return np.sqrt((self.ell / 2.)**2 + (self.y0)**2)

    def goto(self, x, y):
        '''Move payload to position (x,y)'''
        s1 = np.sqrt((self.ell / 2. - x)**2 + y**2)
        s2 = np.sqrt((self.ell / 2. + x)**2 + y**2)
        n1 = np.rint((s1 - self.s0) / self.ds).astype(int)
        n2 = np.rint((self.s0 - s2) / self.ds).astype(int)
        super(QPolargraph, self).goto(n1, n2)

    @pyqtProperty(float, float)
    def position(self):
        '''Current coordinates in meters'''
        n1, n2 = self.indexes
        s1 = self.s0 + n1 * self.ds
        s2 = self.s0 - n2 * self.ds
        x = (s2**2 - s1**2) / (2. * self.ell)
        ysq = (s1**2 + s2**2) / 2. - self.ell**2 / 4. - x**2
        if ysq < 0:
            logger.error(f'unphysical result: {n1} {n2} {self.s0} {s1} {s2} {ysq}')
            y = self.y0
        else:
            y = np.sqrt(ysq)
        return x, y

    @pyqtProperty(float)
    def speed(self):
        '''Translation speed in mm/s'''
        return self.motor_speed * self.circumference * self.pitch / self.steps

    @speed.setter
    def speed(self, value):
        self.motor_speed = value * (self.steps /
                                    (self.circumference * self.pitch))


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication, QWidget
    import sys

    app = QApplication(sys.argv)
    polargraph = QPolargraph()
    print(f'Current position: {polargraph.indexes}')
    polargraph.goto(0.01, -0.01)
    w = QWidget()
    w.show()
    while (polargraph.running):
        print('.')
    polargraph.close()
    sys.exit(app.exec_())
