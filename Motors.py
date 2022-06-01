from QInstrument.lib import QSerialInstrument
from PyQt5.QtCore import pyqtProperty
from time import sleep
import logging

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Motors(QSerialInstrument):

    '''
    Abstraction of stepper moters controlled by Arduino

    ...

    Attributes
    ----------
    indexes : tuple of integers
        (n1, n2) Step indexes of two stepper motors.
        Setting this property causes the motors to move to (n1, n2).
    motor_speed : float
        maximum stepper motor speed in steps/second.

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
        self.send(f'G:{n1}:{n2}')

    def home(self):
        '''Move to home position'''
        self.goto(0, 0)

    def release(self):
        '''Stop and release motors'''
        self.send('S')

    def running(self):
        '''Returns True if motors are running'''
        try:
            res = self.handshake('R')
            header, running = res.split(':')
        except Exception as ex:
            logger.warning(f'Could not read running status: {ex}')
            running = 0
        return bool(int(running))

    @pyqtProperty(int, int)
    def indexes(self):
        '''Current step numbers for motors'''
        try:
            res = self.handshake('P')
            header, n1, n2 = res.split(':')
            n1 = int(n1)
            n2 = int(n2)
        except Exception as ex:
            logger.warning(f'Did not read position: {ex}')
            n1 = 0
            n2 = 0
        return n1, n2

    @indexes.setter
    def indexes(self, n1, n2):
        self.send(f'P:{n1}:{n2}')

    @pyqtProperty(float)
    def motor_speed(self):
        '''Maximum motor speed in steps/sec'''
        try:
            res = self.handshake('V')
            header, speed = res.split(':')
        except Exception as ex:
            logger.warning(f'Could not read maximum speed: {ex}')
            speed = 0
        return float(speed)

    @motor_speed.setter
    def motor_speed(self, speed):
        res = self.handshake(f'V:{speed}')
        logger.debug(f'speed: {res}')
