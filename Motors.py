from QInstrument.lib import QSerialInstrument
from PyQt5.QtCore import pyqtProperty
import numpy as np
from parse import parse
from time import sleep
import logging

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


__version__ = '3.1.0'


class Motors(QSerialInstrument):

    '''
    PyQt5-compatible abstraction of a pair of stepper moters
    controlled by an Arduino

    ...

    Inherits
    --------
    QInstrument.QSerialInstrument

    Properties
    ----------
    indexes : numpy.ndarray(int, int, int)
        (n1, n2): Step indexes of two stepper motors.
        status: 1 if motors are running, 0 otherwise.
        Setting (n1, n2) defines the step counts to be (n1, n2).
    motor_speed : numpy.ndarray(float, float)
        (v1, v2) Maximum stepper motor speed in steps/second.
    acceleration : numpy.ndarray(float, float)
        (a1, a2) Acceleration in steps/second^2.

    Methods
    -------
    goto(n1, n2)
        Set target step counts for stepper motors.  This causes the
        motors to move to the new values.
    home()
        Equivalent to goto(0, 0)
    release()
        Stop motors and turn off current to windings.
    running() : bool
        Returns True if motors are running.
    '''

    settings = dict(baudRate=QSerialInstrument.Baud9600,
                    dataBits=QSerialInstrument.Data8,
                    stopBits=QSerialInstrument.OneStop,
                    parity=QSerialInstrument.NoParity,
                    flowControl=QSerialInstrument.NoFlowControl,
                    eol='\n')

    def __init__(self, portName=None, **kwargs):
        super().__init__(portName, **self.settings, **kwargs)

    def identify(self):
        logger.info(f' Trying {self.portName()}...')
        sleep(2)
        res = self.handshake('Q')
        logger.debug(f' Received: {res}')
        if 'acam' not in res:
            return False
        version = parse('acam{:>}', res)[0]
        if version != __version__:
            logger.error(f' Arduino is running acam3 version {version}')
            logger.error(f' Install version {__version__}')
            return False
        logger.info(f' Arduino running acam {version}')
        return True

    def process(self, data):
        logger.debug(f' received: {data}')

    def goto(self, n1, n2):
        '''Move to index (n1, n2)

        Parameters
        ----------
        n1 : int
            Index of motor 1
        n2 : int
            Index of motor 2
        '''
        logger.debug(f' goto {n1} {n2}')
        ok = self.expect(f'G:{n1}:{n2}', 'G')
        if not ok:
            logger.error(f'Could not set target indexes: ({n1},{n2})')

    def home(self):
        '''Move to home position'''
        self.goto(0, 0)

    def stop(self):
        '''Stop motion'''
        ok = self.expect('S', 'S')
        if not ok:
            logger.error('Error stopping motion')

    def release(self):
        '''De-energize motor coils'''
        ok = self.expect('X', 'X')
        if not ok:
            logger.error('Error releasing stepper motors!')

    def running(self):
        '''Returns True if motors are running'''
        res = self.handshake('R')
        status = res.split(':')[1] if ('R:' in res) else '0'
        return status == '1'

    @pyqtProperty(np.ndarray)
    def indexes(self):
        '''Current step numbers for motors'''
        try:
            status, n1, n2 = self.handshake('P').split(':')
            indexes = [int(n1), int(n2), int(status == 'R')]
            logger.debug(f'{indexes}')
        except Exception as ex:
            logger.warning(f'Did not read position: {ex}')
            indexes = [0, 0, 0]
        return np.array(indexes)

    @indexes.setter
    def indexes(self, n):
        n1, n2 = n
        self.expect(f'P:{n1}:{n2}', 'P')

    @pyqtProperty(np.ndarray)
    def motor_speed(self):
        '''Maximum motor speed [steps/s]'''
        try:
            res = self.handshake('V')
            _, v1, v2 = res.split(':') if 'V:' in res else 0, 0, 0
        except Exception as ex:
            logger.warning(f'Could not read maximum speed: {ex}')
            v1, v2, = 0., 0.
        return np.array([float(v1), float(v2)])

    @motor_speed.setter
    def motor_speed(self, v):
        v1, v2 = v
        ok = self.expect(f'V:{v1}:{v2}', 'V')
        if not ok:
            logger.warning(f'Could not set maximum speed: ({v1},{v2})')

    @pyqtProperty(np.ndarray)
    def acceleration(self):
        '''Acceleration [steps/s^2]'''
        return self._acceleration

    @acceleration.setter
    def acceleration(self, a):
        a1, a2 = a
        self._acceleration = np.array([a1, a2])
        res = self.handshake(f'A:{a1}:{a2}')
        logger.debug(f'acceleration: {res} {a1} {a2}')


def main():
    from PyQt5.QtCore import QCoreApplication
    import sys

    print('Motor subsystem test')
    app = QCoreApplication(sys.argv)
    motors = Motors().find()
    print(f'Current position: {motors.indexes}')
    motors.goto(100, 50)
    if motors.running():
        print('Running...')
    while (motors.running()):
        pass
    print(f'Final position: {motors.indexes}')
    motors.close()
    app.quit()


if __name__ == '__main__':
    main()
