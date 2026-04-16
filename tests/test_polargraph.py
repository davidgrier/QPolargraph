import numpy as np
import pytest
from QPolargraph.fake import FakePolargraph


@pytest.fixture
def pg():
    return FakePolargraph(step_delay=0.)


# --- defaults ---

def test_default_ell(pg):
    assert pg.ell == pytest.approx(1.0)


def test_default_y0(pg):
    assert pg.y0 == pytest.approx(0.1)


def test_default_pitch(pg):
    assert pg.pitch == pytest.approx(2.0)


def test_default_circumference(pg):
    assert pg.circumference == 25


def test_default_steps(pg):
    assert pg.steps == 200


def test_default_speed(pg):
    assert pg.speed == pytest.approx(100.0)


# --- derived geometry ---

def test_ds(pg):
    assert pg.ds == pytest.approx(1e-3 * 2.0 * 25 / 200)


def test_s0(pg):
    assert pg.s0 == pytest.approx(np.sqrt(0.5 ** 2 + 0.1 ** 2))


# --- coordinate conversion ---

def test_i2r_at_home(pg):
    x, y, status = pg.i2r([0, 0, 0])
    assert x == pytest.approx(0.0)
    assert y == pytest.approx(pg.y0)
    assert status == 0


def test_i2r_roundtrip(pg):
    '''moveTo a point then verify i2r recovers it.'''
    xt, yt = 0.05, 0.3
    pg.moveTo(xt, yt)
    n1, n2, _ = pg.indexes
    x, y, _ = pg.i2r([n1, n2, 0])
    assert x == pytest.approx(xt, abs=pg.ds)
    assert y == pytest.approx(yt, abs=pg.ds)


def test_position_at_home(pg):
    x, y, _ = pg.position
    assert x == pytest.approx(0.0)
    assert y == pytest.approx(pg.y0)


# --- property registration ---

def test_registered_properties(pg):
    for name in ('ell', 'y0', 'pitch', 'circumference', 'steps', 'speed'):
        assert name in pg.properties


def test_property_set_get_roundtrip(pg):
    pg.set('ell', 1.5)
    assert pg.get('ell') == pytest.approx(1.5)


def test_property_type_coercion_int(pg):
    pg.set('circumference', 20)
    assert isinstance(pg.get('circumference'), int)


def test_property_type_coercion_float(pg):
    pg.set('speed', 200)
    assert isinstance(pg.get('speed'), float)


# --- moveTo ---

def test_moveto_home_is_zero_indexes(pg):
    pg.moveTo(0.0, pg.y0)
    np.testing.assert_array_equal(pg.indexes, [0, 0, 0])


def test_moveto_updates_motor_speed(pg):
    pg.moveTo(0.1, 0.3)
    v = pg.motor_speed
    assert all(v > 0)


# --- motion simulation ---

def _consume(pg):
    '''Consume the full trajectory, returning all positions.'''
    positions = []
    while True:
        pos = pg.position
        positions.append(pos)
        if not pos[2]:
            break
    return positions


def test_moveto_generates_intermediate_positions(pg):
    pg.moveTo(0.2, 0.4)
    positions = _consume(pg)
    assert len(positions) > 1


def test_moveto_final_position_correct(pg):
    pg.moveTo(0.2, 0.4)
    positions = _consume(pg)
    x, y, running = positions[-1]
    assert running == 0.0
    assert x == pytest.approx(0.2, abs=1e-9)
    assert y == pytest.approx(0.4, abs=1e-9)


def test_moveto_running_flag_while_in_motion(pg):
    pg.moveTo(0.2, 0.4)
    pos = pg.position
    assert pos[2] == 1.0


def test_stop_halts_motion(pg):
    pg.moveTo(0.2, 0.4)
    _ = pg.position   # consume one step (ensure motion started)
    pg.stop()
    pos = pg.position
    assert pos[2] == 0.0


def test_moveto_zero_distance_arrives_immediately(pg):
    x0, y0, _ = pg.position
    pg.moveTo(x0, y0)
    pos = pg.position
    assert pos[2] == 0.0
