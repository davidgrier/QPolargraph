from QPolargraph.Motors import Motors
from PyQt5.QtCore import pyqtProperty
import numpy as np
import logging

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


class Polargraph(Motors):

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
    ell : float
        Separation between motors [m]
    y0 : float
        Vertical displacement of home position [m]
    pitch : float
        Separation between teeth on timing belt [mm]
        Default: 2.
    circumference : float
        Number of teeth per revolution.
        Default: 25.
    steps : float
        Number of motor steps per revolution.
        Default: 200.

    ds : float
        Distance traveled per motor step [mm]
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

    def Property(name, dtype=float):
        pname = f'_{name}'

        def getter(self):
            return dtype(getattr(self, pname))

        def setter(self, value):
            logger.debug(f'Setting {name}: {value}')
            setattr(self, pname, dtype(value))
        return pyqtProperty(dtype, getter, setter)

    pitch = Property('pitch')
    circumference = Property('circumference', int)
    steps = Property('steps', int)
    ell = Property('ell')
    y0 = Property('y0')

    def __init__(self,
                 pitch=2.,          # size of one timing belt tooth [mm]
                 circumference=25,  # belt teeth per revolution
                 steps=200,         # motor steps per revolution
                 ell=1.,            # separation between motors [m]
                 y0=0.1,            # home position [m]
                 **kwargs):

        super().__init__(**kwargs)

        # Belt drive
        self.pitch = pitch
        self.circumference = circumference
        self.steps = steps

        # Motor configuration
        self.ell = ell
        self.y0 = y0

        # Busy status for QInstrumentWidget
        self.busy = self.running

    @pyqtProperty(float)
    def ds(self):
        '''Distance traveled per step [mm]'''
        return self.pitch * self.circumference / self.steps

    @pyqtProperty(float)
    def speed(self):
        '''Translation speed [mm/s]'''
        return self.motor_speed * self.ds

    @speed.setter
    def speed(self, speed):
        self.motor_speed = speed / self.ds

    @pyqtProperty(float)
    def s0(self):
        '''Distance from motor to payload at home position [m]'''
        return np.sqrt((self.ell/2.)**2 + (self.y0)**2)

    @pyqtProperty(float, float)
    def position(self):
        '''Current coordinates [m]'''
        n1, n2 = self.indexes
        s1 = self.s0 + n1*self.ds
        s2 = self.s0 - n2*self.ds
        x = (s2**2 - s1**2)/(2. * self.ell)
        ysq = (s1**2 + s2**2)/2. - self.ell**2/4. - x**2
        if ysq < 0:
            logger.error('unphysical result: ' +
                         f'{n1} {n2} {self.s0} {s1} {s2} {ysq}')
        y = np.sqrt(ysq) if ysq >= 0 else self.y0
        return x, y

    def goto(self, x, y):
        '''Move payload to position (x,y) [m]'''
        s1 = np.sqrt((self.ell/2. - x)**2 + y**2)
        s2 = np.sqrt((self.ell/2. + x)**2 + y**2)
        n1 = np.rint((s1 - self.s0)/self.ds).astype(int)
        n2 = np.rint((self.s0 - s2)/self.ds).astype(int)
        super(Polargraph, self).goto(n1, n2)


def demo():
    from PyQt5.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    polargraph = Polargraph().find()
    print(f'Current position: {polargraph.indexes}')
    polargraph.goto(0.01, -0.01)
    if polargraph.running:
        print('Running...')
    while (polargraph.running):
        pass
    print(f'Current position: {polargraph.indexes}')
    polargraph.close()
    sys.exit(app.exec_())


if __name__ == '__main__':
    demo()
