from QInstrument.lib.QFakeInstrument import QFakeInstrument
from QPolargraph.Motors import Motors
from QPolargraph.Polargraph import Polargraph
import numpy as np
import logging


logger = logging.getLogger(__name__)


class FakeMotors(QFakeInstrument, Motors):
    '''Fake stepper-motor controller for development without hardware.

    Stores step indexes and motor speeds in memory.  :meth:`goto`
    updates the stored indexes immediately.  :meth:`running` always
    returns ``False``.
    '''

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._acceleration = np.zeros(2)

    def identify(self) -> bool:
        return True

    @property
    def indexes(self) -> np.ndarray:
        return np.array(self._store.get('indexes', [0, 0, 0]))

    @indexes.setter
    def indexes(self, n) -> None:
        n1, n2 = n
        self._store['indexes'] = [int(n1), int(n2), 0]

    @property
    def motor_speed(self) -> np.ndarray:
        return np.array(self._store.get('motor_speed', [0., 0.]))

    @motor_speed.setter
    def motor_speed(self, v) -> None:
        v1, v2 = v
        self._store['motor_speed'] = [float(v1), float(v2)]

    @property
    def acceleration(self) -> np.ndarray:
        return self._acceleration

    @acceleration.setter
    def acceleration(self, a) -> None:
        a1, a2 = a
        self._acceleration = np.array([float(a1), float(a2)])

    def goto(self, n1: int, n2: int) -> None:
        self._store['indexes'] = [int(n1), int(n2), 0]

    def running(self) -> bool:
        return False

    def stop(self) -> None:
        pass

    def release(self) -> None:
        pass

    def close(self) -> None:
        pass


class FakePolargraph(FakeMotors, Polargraph):
    '''Fake polargraph scanner for development without hardware.

    Combines :class:`FakeMotors` in-memory I/O with
    :class:`Polargraph` belt-drive geometry.  All scalar properties
    (``ell``, ``y0``, ``pitch``, ``circumference``, ``steps``,
    ``speed``) are initialised to the same defaults as the real
    instrument and are fully readable and writable.
    :meth:`~Polargraph.moveTo` and :meth:`~Polargraph.i2r` work
    correctly since they depend only on those scalar properties and
    the in-memory ``indexes``.
    '''

    def __init__(self,
                 pitch: float = 2.,
                 circumference: int = 25,
                 steps: int = 200,
                 ell: float = 1.,
                 y0: float = 0.1,
                 speed: float = 100.,
                 **kwargs) -> None:
        super().__init__(**kwargs)
        self.pitch = pitch
        self.circumference = circumference
        self.steps = steps
        self.ell = ell
        self.y0 = y0
        self.speed = speed


__all__ = ['FakePolargraph', 'FakeMotors']
