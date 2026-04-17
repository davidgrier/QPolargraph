import numpy as np
import pytest
from QPolargraph.hardware.fake import FakeMotors


@pytest.fixture
def motors():
    return FakeMotors()


def test_is_open(motors):
    assert motors.isOpen()


def test_identify(motors):
    assert motors.identify()


def test_indexes_default(motors):
    np.testing.assert_array_equal(motors.indexes, [0, 0, 0])


def test_motor_speed_default(motors):
    np.testing.assert_array_equal(motors.motor_speed, [0., 0.])


def test_acceleration_default(motors):
    np.testing.assert_array_equal(motors.acceleration, [0., 0.])


def test_running_false(motors):
    assert not motors.running()


def test_goto(motors):
    motors.goto(10, 20)
    np.testing.assert_array_equal(motors.indexes, [10, 20, 0])


def test_home_resets_indexes(motors):
    motors.goto(100, 200)
    motors.home()
    np.testing.assert_array_equal(motors.indexes, [0, 0, 0])


def test_motor_speed_setter(motors):
    motors.motor_speed = [300., 400.]
    np.testing.assert_array_almost_equal(motors.motor_speed, [300., 400.])


def test_acceleration_setter(motors):
    motors.acceleration = [50., 75.]
    np.testing.assert_array_almost_equal(motors.acceleration, [50., 75.])


def test_indexes_setter(motors):
    motors.indexes = (50, 75)
    np.testing.assert_array_equal(motors.indexes, [50, 75, 0])


def test_stop_is_noop(motors):
    motors.goto(100, 100)
    motors.stop()
    np.testing.assert_array_equal(motors.indexes, [100, 100, 0])


def test_release_does_not_raise(motors):
    motors.release()


def test_close_does_not_raise(motors):
    motors.close()


def test_firmware_version():
    assert FakeMotors.FIRMWARE_VERSION == '3.3.0'
