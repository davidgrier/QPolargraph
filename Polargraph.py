from QPolargraph.Motors import Motors
from PyQt5.QtCore import pyqtProperty
import numpy as np
import logging

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


class Polargraph(Motors):

    '''
    PyQt5-compatible abstraction of a polargraph

    The polargraph consists of two stepper motors with GT2 gears
    that translate a GT2 timing belt.  The motors are controlled
    by an Arduino microcontroller that is connected to the host
    computer by USB.  This class communicates with the Arduino
    to control the motion.

    ...

    Inherits
    --------
    QPolargraph.Motors

    Properties
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
    position : numpy.ndarray(float, float)
       Report current coordinates of payload measured in
       meters from home position.
    speed : float
       Maximum translation speed [mm/s]
    acceleration : float
       Maximum acceleration [mm/s^2]

    Methods
    -------
    moveTo(x, y)
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
    speed = Property('speed')
    acceleration = Property('acceleration')

    def __init__(self,
                 pitch=2.,          # size of one timing belt tooth [mm]
                 circumference=25,  # belt teeth per revolution
                 steps=200,         # motor steps per revolution
                 ell=1.,            # separation between motors [m]
                 y0=0.1,            # home position [m]
                 speed=100.,        # desired speed [steps/s]
                 **kwargs):

        super().__init__(**kwargs)

        # Belt drive
        self.pitch = pitch
        self.circumference = circumference
        self.steps = steps

        # Motor configuration
        self.ell = ell
        self.y0 = y0
        self.speed = speed

    @pyqtProperty(float)
    def ds(self):
        '''Distance traveled per step [m]'''
        return 1e-3 * self.pitch * self.circumference / self.steps

    @pyqtProperty(float)
    def s0(self):
        '''Distance from motor to payload at home position [m]'''
        return np.sqrt((self.ell/2.)**2 + (self.y0)**2)

    def i2r(self, indexes):
        '''Convert motor indexes to coordinates [m]'''
        m, n, status = indexes
        sm = self.s0 + m*self.ds
        sn = self.s0 - n*self.ds
        x = (sm**2 - sn**2)/(2. * self.ell)
        ysq = (sn**2 + sm**2)/2. - self.ell**2/4. - x**2
        if ysq < 0:
            logger.error('unphysical result: ' +
                         f'{m} {n} {self.s0} {sm} {sn} {ysq}')
        y = np.sqrt(ysq) if ysq >= 0 else self.y0
        return np.array([x, y, status])

    @pyqtProperty(np.ndarray)
    def position(self):
        '''Current coordinates [m]'''
        return self.i2r(self.indexes)

    def moveTo(self, x, y):
        '''Move payload to position (x,y) [m]'''
        # current motor indexes
        m0, n0, running = self.indexes
        # target motor indexes
        sm = np.sqrt((self.ell/2. + x)**2 + y**2)
        sn = np.sqrt((self.ell/2. - x)**2 + y**2)
        m1 = np.rint((sm - self.s0)/self.ds).astype(int)
        n1 = np.rint((self.s0 - sn)/self.ds).astype(int)

        # adjust speed so that motors complete motion simulutaneously
        if (m0 == m1) or (n0 == n1):
            vm, vn = self.speed, self.speed
        else:
            f = (float(n1-n0)/float(m1-m0))**2
            vn = self.speed / np.sqrt(1. + f)
            vm = np.sqrt(f)*vn
        logger.debug(f'Motor speeds: ({vm}, {vn})')
        self.motor_speed = [vm, vn]
        # go to target indexes
        logger.debug(f'Path: ({m0}, {n0}) --> ({m1}, {n1})')
        self.goto(m1, n1)


def main():
    from PyQt5.QtCore import QCoreApplication
    import sys

    print('Polargraph test')
    app = QCoreApplication(sys.argv)
    polargraph = Polargraph().find()
    print(f'Current position: {polargraph.indexes}')
    polargraph.moveTo(0.0, 100)
    if polargraph.running():
        print('Running...')
    while (polargraph.running()):
        pass
    print(f'Current position: {polargraph.indexes}')
    polargraph.close()
    app.quit()


if __name__ == '__main__':
    main()
