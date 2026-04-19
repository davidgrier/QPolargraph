'''Motors — serial abstraction for two Arduino-driven stepper motors.

Hardware requirements
---------------------
Arduino
    Any Arduino with a USB serial port and I2C support (Uno, Mega, etc.).
    The board must be flashed with the ``acam3`` firmware bundled at
    ``hardware/arduino/acam3/acam3.ino``.

Adafruit Motor Shield v2
    The shield (I2C address ``0x60``) must be seated on the Arduino.
    It drives two stepper motors via the ``Adafruit_MotorShield`` library.
    Standard 200-step-per-revolution motors are assumed.

Arduino libraries
    ``acam3.ino`` requires the following Arduino libraries:

    - ``Adafruit Motor Shield V2 Library``
    - ``AccelStepper``

    :mod:`~QPolargraph.FlashFirmware` installs them automatically before
    compiling.  To install manually via the Arduino IDE Library Manager
    or ``arduino-cli``::

        arduino-cli lib install "Adafruit Motor Shield V2 Library"
        arduino-cli lib install "AccelStepper"

Flashing the firmware
---------------------
Use the :mod:`~QPolargraph.FlashFirmware` module to detect an attached
Arduino and upload ``acam3.ino`` without opening the Arduino IDE::

    qpolargraph-flash

Or from Python:

.. code-block:: python

    from QPolargraph.FlashFirmware import FlashDialog
    FlashDialog().exec()

See :mod:`QPolargraph.FlashFirmware` for integration into a
``QMainWindow`` application via a menu action.
'''

from QInstrument.lib.QSerialInstrument import QSerialInstrument
from qtpy import QtCore
import numpy as np
from parse import parse
from pathlib import Path
from time import sleep
import logging
import re


logger = logging.getLogger(__name__)


def _firmware_version() -> str:
    ino = Path(__file__).parent / 'arduino' / 'acam3' / 'acam3.ino'
    pattern = re.compile(r'#define\s+VERSION\s+"acam(\S+)"')
    with ino.open() as f:
        for line in f:
            if m := pattern.match(line.strip()):
                return m.group(1)
    raise RuntimeError('VERSION not found in acam3.ino')


class Motors(QSerialInstrument):

    '''Abstraction of a pair of stepper motors controlled by an Arduino.

    Communicates with an Arduino running the acam3 firmware over USB
    serial. The Arduino drives two stepper motors via an Adafruit Motor
    Shield.

    Properties
    ----------
    indexes : numpy.ndarray
        ``(n1, n2, status)`` — step indexes of the two stepper motors
        and a running flag (1 while moving, 0 when stopped).
        Setting ``(n1, n2)`` redefines the step-count origin.
    motor_speed : numpy.ndarray
        ``(v1, v2)`` — maximum stepper motor speed [steps/s].
    acceleration : numpy.ndarray
        ``(a1, a2)`` — acceleration [steps/s²].

    Methods
    -------
    goto(n1, n2)
        Move to target step counts ``(n1, n2)``.
    home()
        Equivalent to ``goto(0, 0)``.
    stop()
        Halt motion immediately.
    release()
        Stop motors and de-energise the windings.
    running()
        Return ``True`` if the motors are currently moving.
    '''

    FIRMWARE_VERSION = _firmware_version()

    comm = dict(baudRate=QSerialInstrument.BaudRate.Baud115200,
                dataBits=QSerialInstrument.DataBits.Data8,
                stopBits=QSerialInstrument.StopBits.OneStop,
                parity=QSerialInstrument.Parity.NoParity,
                flowControl=QSerialInstrument.FlowControl.NoFlowControl,
                eol='\n')

    def __init__(self, portName: str | None = None, **kwargs):
        super().__init__(portName, **(self.comm | kwargs))
        self._acceleration = np.zeros(2)

    def _registerProperties(self) -> None:
        super()._registerProperties()

    def _registerMethods(self) -> None:
        super()._registerMethods()
        self.registerMethod('home', self.home)
        self.registerMethod('stop', self.stop)
        self.registerMethod('release', self.release)

    def identify(self) -> bool:
        '''Return ``True`` if
        (1) the port responds with the correct acam3 version string, and
        (2) the Adafruit Motor Shield is detected.

        Waits 2 s after opening for the Arduino to reset, then sends ``Q``
        and checks that the response is ``acam{FIRMWARE_VERSION}:OK``.
        A response of ``acam{FIRMWARE_VERSION}:NOSHIELD`` indicates that the
        Adafruit Motor Shield was not detected at I2C address ``0x60``.
        '''
        logger.info(f' Trying {self._interface.portName()}...')
        sleep(2)
        res = self.handshake('Q')
        logger.debug(f' Received: {res}')
        if 'acam' not in res:
            return False
        result = parse('acam{:>}:{:>}', res)
        if result is None:
            return False
        fw_version, shield_status = result
        if fw_version != self.FIRMWARE_VERSION:
            logger.error(f' Arduino is running acam3 version {fw_version}')
            logger.error(f' Install version {self.FIRMWARE_VERSION}')
            return False
        if shield_status != 'OK':
            logger.error(' Adafruit Motor Shield not detected (I2C address 0x60)')
            logger.error(' Check that the shield is fully seated on the Arduino')
            logger.error(' and re-flash the firmware if the problem persists')
            return False
        logger.info(f' Arduino running acam {fw_version}, motor shield OK')
        return True

    def process(self, data: str) -> None:
        logger.debug(f' received: {data}')

    def goto(self, n1: int, n2: int) -> None:
        '''Move to target step counts.

        Parameters
        ----------
        n1 : int
            Target step index for motor 1.
        n2 : int
            Target step index for motor 2.
        '''
        logger.debug(f' goto {n1} {n2}')
        ok = self.expect(f'G:{n1}:{n2}', 'G')
        if not ok:
            logger.error(f'Could not set target indexes: ({n1},{n2})')

    def home(self) -> None:
        '''Move to home position (step index 0, 0).'''
        self.goto(0, 0)

    def stop(self) -> None:
        '''Halt motor motion immediately.'''
        ok = self.expect('S', 'S')
        if not ok:
            logger.error('Error stopping motion')

    def release(self) -> None:
        '''De-energise motor coils.'''
        ok = self.expect('X', 'X')
        if not ok:
            logger.error('Error releasing stepper motors!')

    def running(self) -> bool:
        '''Return ``True`` if the motors are currently moving.'''
        if not self.isOpen():
            return False
        res = self.handshake('R')
        status = res.split(':')[1] if ('R:' in res) else '0'
        return status == '1'

    @property
    def indexes(self) -> np.ndarray:
        '''Current step counts ``(n1, n2, status)`` for both motors.'''
        if not self.isOpen():
            return np.array([0, 0, 0])
        try:
            _, n1, n2, running = self.handshake('P').split(':')
            indexes = [int(n1), int(n2), int(running)]
            logger.debug(f'{indexes}')
        except Exception as ex:
            logger.warning(f'Did not read position: {ex}')
            indexes = [0, 0, 0]
        return np.array(indexes)

    @indexes.setter
    def indexes(self, n) -> None:
        n1, n2 = n
        self.expect(f'P:{n1}:{n2}', 'P')

    @property
    def motor_speed(self) -> np.ndarray:
        '''Maximum motor speed ``(v1, v2)`` [steps/s].'''
        try:
            res = self.handshake('V')
            _, v1, v2 = res.split(':') if 'V:' in res else (0, 0, 0)
        except Exception as ex:
            logger.warning(f'Could not read maximum speed: {ex}')
            v1, v2 = 0., 0.
        return np.array([float(v1), float(v2)])

    @motor_speed.setter
    def motor_speed(self, v) -> None:
        v1, v2 = v
        ok = self.expect(f'V:{v1}:{v2}', 'V')
        if not ok:
            logger.warning(f'Could not set maximum speed: ({v1},{v2})')

    @property
    def acceleration(self) -> np.ndarray:
        '''Motor acceleration ``(a1, a2)`` [steps/s²].'''
        return self._acceleration

    @acceleration.setter
    def acceleration(self, a) -> None:
        a1, a2 = a
        self._acceleration = np.array([a1, a2])
        res = self.handshake(f'A:{a1}:{a2}')
        logger.debug(f'acceleration: {res} {a1} {a2}')


def main():
    from qtpy.QtCore import QCoreApplication
    import sys

    print('Motor subsystem test')
    app = QCoreApplication(sys.argv)
    motors = Motors().find()
    if not motors.isOpen():
        print('No Motors found. Using FakeMotors.')
        from QPolargraph.hardware.fake import FakeMotors
        motors = FakeMotors()
    print(f'Current position: {motors.indexes}')
    motors.goto(100, 50)
    if motors.running():
        print('Running...')
    while motors.running():
        pass
    print(f'Final position: {motors.indexes}')
    motors.close()
    app.quit()


if __name__ == '__main__':
    main()
