from QInstrument.lib import QSerialInstrument
from PyQt5.QtCore import pyqtProperty
from time import sleep
import logging

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


class Motors(QSerialInstrument):

    '''
    Abstraction of stepper moters controlled by Arduino

    ...

    Attributes
    ----------
    indexes : (int, int)
        (n1, n2) Step indexes of two stepper motors.
        Setting this property causes the motors to move to (n1, n2).
    motor_speed : (float, float)
        (v1, v2) Maximum stepper motor speed in steps/second.
    acceleration : (float, float)
        (a1, a2) Acceleration in steps/second^2.

    Methods
    -------
    goto(n1, n2)
        Set target indexes for stepper motors.  This causes the
        motors to move from their present indexes to the new values.
    home()
        Equivalent to goto(0, 0)
    release()
        Stop motors and turn off current to windings.
    running() : bool
        Returns True if motors are running.
    '''

    settings = dict(baudRate=QSerialInstrument.Baud115200,
                    dataBits=QSerialInstrument.Data8,
                    stopBits=QSerialInstrument.OneStop,
                    parity=QSerialInstrument.NoParity,
                    flowControl=QSerialInstrument.NoFlowControl,
                    eol='\n')

    def __init__(self, portName=None, **kwargs):
        super().__init__(portName, **self.settings, **kwargs)

    def identify(self):
        version = 'acam3'
        logger.info(f' Trying {self.portName()}...')
        sleep(2)
        res = self.handshake('Q')
        logger.debug(f' Received: {res}')
        acam = version in res
        logger.info(f' Arduino running {version}: {acam}')
        return acam

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
        self.handshake(f'G:{n1}:{n2}')

    def home(self):
        '''Move to home position'''
        self.goto(0, 0)

    def release(self):
        '''Stop and release motors'''
        self.send('S')

    def running(self):
        '''Returns True if motors are running'''
        res = self.handshake('R')
        logger.debug(f'running: {res}')
        _, running = res.split(':') if 'R:' in res else 0, 0
        return running == '1'

    @pyqtProperty(int, int)
    def indexes(self):
        '''Current step numbers for motors'''
        try:
            res = self.handshake('P')
            _, n1, n2 = res.split(':') if 'P:' in res else 0, 0, 0
        except Exception as ex:
            logger.warning(f'Did not read position: {ex}')
            n1 = 0
            n2 = 0
        return int(n1), int(n2)

    @indexes.setter
    def indexes(self, n):
        n1, n2 = n
        self.send(f'P:{n1}:{n2}')

    @pyqtProperty(float, float)
    def motor_speed(self):
        '''Maximum motor speed [steps/s]'''
        try:
            res = self.handshake('V')
            _, v1, v2 = res.split(':') if 'V:' in res else 0, 0, 0
        except Exception as ex:
            logger.warning(f'Could not read maximum speed: {ex}')
            v1, v2, = 0., 0.
        return float(v1), float(v2)

    @motor_speed.setter
    def motor_speed(self, v):
        v1, v2 = v
        res = self.handshake(f'V:{v1}:{v2}')
        logger.debug(f'speed: {res} {v1} {v2}')

    @pyqtProperty(float, float)
    def acceleration(self):
        '''Acceleration [steps/s^2]'''
        return self._acceleration

    @acceleration.setter
    def acceleration(self, a):
        a1, a2 = a
        self._acceleration = (a1, a2)
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
