from qtpy import QtCore
from QPolargraph.hardware.Motors import Motors
import numpy as np
import logging


logger = logging.getLogger(__name__)


class Polargraph(Motors):

    '''Base implementation for a polargraph scanner.

    Extends :class:`Motors` with the belt-drive geometry to convert
    between motor step-index space and Cartesian coordinates in metres.
    The payload hangs from the midpoint of a GT2 timing belt whose ends
    are wound on toothed gears driven by two Nema-17 stepper motors
    mounted above and to either side of the scan area.

    Properties
    ----------
    ell : float
        Separation between the two motor pulleys [m].
    y0 : float
        Vertical distance from the pulleys to the home position [m].
    pitch : float
        Tooth pitch of the GT2 timing belt [mm]. Default: 2.
    circumference : int
        Number of belt teeth per full revolution of the gear. Default: 25.
    steps : int
        Motor steps per revolution. Default: 200.
    speed : float
        Maximum translation speed [mm/s].
    ds : float
        Distance travelled per motor step [m]. Read-only.
    s0 : float
        Belt length from pulley to payload at home position [m]. Read-only.
    position : numpy.ndarray
        Current Cartesian coordinates ``(x, y, running)`` [m, m, flag].
        Read-only.

    Methods
    -------
    moveTo(x, y)
        Move the payload to coordinates ``(x, y)`` [m] measured from
        the home position, adjusting motor speeds so both arrive
        simultaneously.

    References
    ----------
    H. W. Gao, K. I. Mishra, A. Winters, S. Wolin, and D. G. Grier,
    "Flexible wide-field high-resolution scanning camera for
    continuous-wave acoustic holography,"
    *Rev. Sci. Instrum.* **89**, 114901 (2018).
    https://doi.org/10.1063/1.5053666
    '''

    def __init__(self,
                 pitch: float = 2.,
                 circumference: int = 25,
                 steps: int = 200,
                 ell: float = 1.,
                 y0: float = 0.1,
                 speed: float = 100.,
                 **kwargs):
        super().__init__(**kwargs)
        self.pitch = pitch
        self.circumference = circumference
        self.steps = steps
        self.ell = ell
        self.y0 = y0
        self.speed = speed

    def _registerProperties(self) -> None:
        super()._registerProperties()
        self.registerProperty('pitch', ptype=float)
        self.registerProperty('circumference', ptype=int)
        self.registerProperty('steps', ptype=int)
        self.registerProperty('ell', ptype=float)
        self.registerProperty('y0', ptype=float)
        self.registerProperty('speed', ptype=float)

    @property
    def pitch(self) -> float:
        '''Tooth pitch of the GT2 timing belt [mm].'''
        return self._pitch

    @pitch.setter
    def pitch(self, value: float) -> None:
        self._pitch = float(value)

    @property
    def circumference(self) -> int:
        '''Number of belt teeth per full revolution of the gear.'''
        return self._circumference

    @circumference.setter
    def circumference(self, value: int) -> None:
        self._circumference = int(value)

    @property
    def steps(self) -> int:
        '''Motor steps per revolution.'''
        return self._steps

    @steps.setter
    def steps(self, value: int) -> None:
        self._steps = int(value)

    @property
    def ell(self) -> float:
        '''Separation between the two motor pulleys [m].'''
        return self._ell

    @ell.setter
    def ell(self, value: float) -> None:
        self._ell = float(value)

    @property
    def y0(self) -> float:
        '''Vertical distance from the pulleys to the home position [m].'''
        return self._y0

    @y0.setter
    def y0(self, value: float) -> None:
        self._y0 = float(value)

    @property
    def speed(self) -> float:
        '''Maximum translation speed [mm/s].'''
        return self._speed

    @speed.setter
    def speed(self, value: float) -> None:
        self._speed = float(value)

    @property
    def ds(self) -> float:
        '''Distance travelled per motor step [m].'''
        return 1e-3 * self.pitch * self.circumference / self.steps

    @property
    def s0(self) -> float:
        '''Belt length from pulley to payload at the home position [m].'''
        return np.hypot(self.ell/2., self.y0)

    def r2f(self, x: float, y: float) -> tuple(float, float):
        '''Convert Cartesian coordinates to continuous step indexes.

        This is the exact (non-rounded) inverse of :meth:`i2r`, useful
        for trajectory interpolation.  To obtain integer motor targets
        suitable for :meth:`goto`, round the result.

        Parameters
        ----------
        x : float
            Horizontal coordinate [m].
        y : float
            Vertical coordinate [m].

        Returns
        -------
        tuple
            ``(m, n)`` step indexes as floats.
        '''
        sm = np.hypot(self.ell/2. + x, y)
        sn = np.hypot(self.ell/2. - x, y)
        m = (sm - self.s0) / self.ds
        n = (self.s0 - sn) / self.ds
        return m, n

    def r2i(self, x: float, y: float) -> tuple(int, int):
        '''Convert Cartesian coordinates to integer motor step indexes.

        Parameters
        ----------
        x : float
            Horizontal coordinate [m].
        y : float
            Vertical coordinate [m].

        Returns
        -------
        tuple
            ``(m, n)`` step indexes as integers.
        '''
        return np.rint(self.r2f(x, y)).astype(int)

    def i2r(self, m: int | float, n: int | float, *args) -> np.ndarray:
        '''Convert motor step indexes to Cartesian coordinates [m].

        Parameters
        ----------
        m: int or float
            Step index for motor 1.
        n: int or float
            Step index for motor 2.

        Returns
        -------
        numpy.ndarray
            ``(x, y, status)`` Cartesian position [m] and running flag.
        '''
        sm = self.s0 + m * self.ds
        sn = self.s0 - n * self.ds
        x = (sm + sn) * (sm - sn) / (2. * self.ell)
        ysq = (sn*sn + sm*sm)/2. - (self.ell/2.)**2 - x*x
        if ysq < 0:
            logger.error('unphysical result: '
                         f'{m} {n} {self.s0} {sm} {sn} {ysq}')
        y = np.sqrt(ysq) if ysq >= 0 else self.y0
        return np.array([x, y, *args])

    @property
    def position(self) -> np.ndarray:
        '''Returns current Cartesian coordinates and a running flag'''
        return self.i2r(*self.indexes)

    @QtCore.Slot(float, float)
    def moveTo(self, x: float, y: float) -> None:
        '''Move the payload to position ``(x, y)`` [m].

        Computes the target step indexes and adjusts both motor speeds
        so they complete their moves simultaneously.

        Parameters
        ----------
        x : float
            Target horizontal coordinate [m].
        y : float
            Target vertical coordinate [m].
        '''
        m0, n0, _ = self.indexes
        m1, n1 = self.r2i(x, y)

        if m0 == m1 or n0 == n1:
            vm, vn = self.speed, self.speed
        else:
            f = (float(n1 - n0) / float(m1 - m0)) ** 2
            vn = self.speed / np.sqrt(1. + f)
            vm = np.sqrt(f) * vn
        logger.debug(f'Motor speeds: ({vm}, {vn})')
        self.motor_speed = [vm, vn]
        logger.debug(f'Path: ({m0}, {n0}) --> ({m1}, {n1})')
        self.goto(m1, n1)


def main():
    from qtpy.QtCore import QCoreApplication
    import sys

    print('Polargraph test')
    app = QCoreApplication(sys.argv)
    polargraph = Polargraph().find()
    if not polargraph.isOpen():
        print('No Polargraph found. Using FakePolargraph.')
        from QPolargraph.hardware.fake import FakePolargraph
        polargraph = FakePolargraph()
    print(f'Current position: {polargraph.indexes}')
    polargraph.moveTo(0., 0.25)
    print('Running...')
    while polargraph.running():
        print(f'Current position: {polargraph.indexes}', end='\r')
        QtCore.QThread.msleep(100)
    print(f'Arrived:          {polargraph.indexes}')
    print('Moving back to home...')
    polargraph.moveTo(0., 0.)
    while polargraph.running():
        print(f'Current position: {polargraph.indexes}', end='\r')
        QtCore.QThread.msleep(100)
    print(f'Final position:      {polargraph.indexes}')
    # TODO: In tests with real hardware, the polargraph returns
    # consistently to position [-40, 40, 0] instead of [0, 0, 0].
    # This is a software bug, not a hardware issue.
    polargraph.close()
    app.quit()


if __name__ == '__main__':
    main()
