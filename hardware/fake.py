import time
from collections import deque
from QInstrument.lib.QFakeInstrument import QFakeInstrument
from QPolargraph.hardware.Motors import Motors
from QPolargraph.hardware.Polargraph import Polargraph
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

    Unlike :class:`FakeMotors`, :meth:`moveTo` simulates belt motion by
    building a Cartesian trajectory at step resolution.  Each call to
    :attr:`position` advances one step along that trajectory, with
    ``position[2] == 1`` while in motion and ``0`` on arrival.  This
    lets :class:`~QPolargraph.QScanPattern.QScanPattern` run a full
    scan loop and emit :attr:`~QScanPattern.dataReady` without real
    hardware.
    '''

    def __init__(self,
                 pitch: float = 2.,
                 circumference: int = 25,
                 steps: int = 200,
                 ell: float = 1.,
                 y0: float = 0.1,
                 speed: float = 100.,
                 step_delay: float = 0.033,
                 **kwargs) -> None:
        super().__init__(**kwargs)
        self.pitch = pitch
        self.circumference = circumference
        self.steps = steps
        self.ell = ell
        self.y0 = y0
        self.speed = speed
        self.step_delay = step_delay
        self._cartesian_trajectory: deque = deque()

    def moveTo(self, x: float, y: float) -> None:
        '''Move to ``(x, y)`` [m], building an intermediate trajectory.

        Generates up to 10 waypoints by interpolating linearly in
        motor step-index space and converting back to Cartesian via
        :meth:`i2r`.  This matches the real hardware, where both motors
        run at constant (but different) speeds so they arrive
        simultaneously, tracing an arc rather than a straight line.
        Subsequent calls to :attr:`position` consume the trajectory one
        step at a time, returning ``running=1`` until the final step.

        Set :attr:`step_delay` to a positive value (seconds) to
        throttle playback and produce smooth belt animation in the UI.
        The default of ``0`` runs as fast as possible, which is
        appropriate for automated tests.

        Parameters
        ----------
        x : float
            Target horizontal coordinate [m].
        y : float
            Target vertical coordinate [m].
        '''
        m0, n0, _ = self._store.get('indexes', [0, 0, 0])
        x0, y0, _ = self.i2r([m0, n0, 0])
        dist = np.hypot(x - x0, y - y0)
        nsteps = max(1, min(10, round(dist / self.ds)))
        m1, n1 = self.r2i(x, y)
        ms = np.linspace(m0, m1, nsteps + 1)[1:]
        ns = np.linspace(n0, n1, nsteps + 1)[1:]
        trajectory = [self.i2r([m, n, 0])[:2].tolist() for m, n in zip(ms, ns)]
        self._cartesian_trajectory = deque(trajectory)
        super().moveTo(x, y)

    @property
    def position(self) -> np.ndarray:
        '''Current Cartesian coordinates ``(x, y, running)`` [m, m, flag].

        While a trajectory is in progress, advances one step per call
        and returns ``running=1``.  Returns ``running=0`` on the final
        step, after which subsequent calls return the stored position.
        If :attr:`step_delay` is positive, sleeps that many seconds
        before advancing, throttling playback to simulate hardware
        timing.
        '''
        if self._cartesian_trajectory:
            if self.step_delay > 0:
                time.sleep(self.step_delay)
            x, y = self._cartesian_trajectory.popleft()
            running = float(bool(self._cartesian_trajectory))
            return np.array([x, y, running])
        return self.i2r(self._store.get('indexes', [0, 0, 0]))

    def stop(self) -> None:
        '''Halt motion by discarding the remaining trajectory.'''
        self._cartesian_trajectory.clear()


__all__ = ['FakePolargraph', 'FakeMotors']
