import numpy as np
import pytest
from QPolargraph.hardware.fake import FakePolargraph
from QPolargraph.patterns.QScanPattern import QScanPattern
from QPolargraph.patterns.RasterScan import RasterScan
from QPolargraph.patterns.PolarScan import PolarScan
from QPolargraph.patterns.TarzanScan import TarzanScan


@pytest.fixture
def pg():
    return FakePolargraph(step_delay=0.)


@pytest.fixture
def scan(pg):
    return QScanPattern(polargraph=pg)


@pytest.fixture
def raster(pg):
    return RasterScan(polargraph=pg)


@pytest.fixture
def polar(pg):
    return PolarScan(polargraph=pg)


@pytest.fixture
def tarzan(pg):
    # Start near the left edge so at least one full cycle fits
    scan = TarzanScan(polargraph=pg)
    x_left = scan.dx - scan.width / 2.
    scan.x0 = x_left + 0.02
    return scan


# --- QScanPattern ---

def test_is_open(scan):
    assert scan.isOpen()


def test_rect_x_bounds(scan):
    x1, y1, x2, y2 = scan.rect()
    assert x1 == pytest.approx(-scan.width / 2)
    assert x2 == pytest.approx(scan.width / 2)


def test_rect_y_bounds(scan):
    x1, y1, x2, y2 = scan.rect()
    assert y1 == pytest.approx(scan.polargraph.y0 + scan.dy)
    assert y2 == pytest.approx(y1 + scan.height)


def test_base_vertices_shape(scan):
    v = scan.vertices()
    assert v.ndim == 2
    assert v.shape[1] == 2


def test_base_vertices_closes_rectangle(scan):
    v = scan.vertices()
    np.testing.assert_array_almost_equal(v[0], v[-1])


def test_base_trajectory_shape(scan):
    t = scan.trajectory()
    assert t.ndim == 2
    assert t.shape[0] == 2


# --- RasterScan ---

def test_raster_vertices_shape(raster):
    v = raster.vertices()
    assert v.ndim == 2
    assert v.shape[1] == 2


def test_raster_x_within_rect(raster):
    v = raster.vertices()
    x1, _, x2, _ = raster.rect()
    assert v[:, 0].min() >= x1 - 1e-9
    assert v[:, 0].max() <= x2 + 1e-9


def test_raster_alternating_y(raster):
    v = raster.vertices()
    _, y1, _, y2 = raster.rect()
    assert v[0, 1] == pytest.approx(y1)
    assert v[1, 1] == pytest.approx(y2)


def test_raster_trajectory_shape(raster):
    t = raster.trajectory()
    assert t.shape[0] == 2


def test_raster_trajectory_has_more_points_than_vertices(raster):
    v = raster.vertices()
    t = raster.trajectory()
    assert t.shape[1] > v.shape[0]


def test_raster_trajectory_starts_at_first_vertex(raster):
    v = raster.vertices()
    t = raster.trajectory()
    assert t[0, 0] == pytest.approx(v[0, 0], abs=1e-6)
    assert t[1, 0] == pytest.approx(v[0, 1], abs=1e-6)


def test_raster_trajectory_ends_at_last_vertex(raster):
    v = raster.vertices()
    t = raster.trajectory()
    assert t[0, -1] == pytest.approx(v[-1, 0], abs=1e-6)
    assert t[1, -1] == pytest.approx(v[-1, 1], abs=1e-6)


def test_raster_trajectory_is_curved(raster):
    '''Trajectory points between two endpoints are not collinear.'''
    t = raster.trajectory()
    # Take first segment: check that intermediate points deviate from
    # the straight line joining the first and last points of that segment.
    n = raster._TRAJECTORY_PTS
    x0, y0 = t[0, 0], t[1, 0]
    x1, y1 = t[0, n - 1], t[1, n - 1]
    # Midpoint on the straight line
    xm_line = (x0 + x1) / 2.
    ym_line = (y0 + y1) / 2.
    # Actual midpoint of the trajectory
    mid = n // 2
    xm_actual = t[0, mid]
    ym_actual = t[1, mid]
    deviation = np.hypot(xm_actual - xm_line, ym_actual - ym_line)
    assert deviation > 1e-6




# --- PolarScan ---

def test_polar_radii_increasing(polar):
    r = polar._radii()
    assert len(r) > 0
    assert (np.diff(r) > 0).all()


def test_polar_radii_step(polar):
    r = polar._radii()
    assert np.diff(r) == pytest.approx(polar.step * 1e-3)


def test_polar_intercepts_returns_two_points(polar):
    r = polar._radii()[0]
    pts = polar._intercepts(r)
    assert len(pts) == 2
    for pt in pts:
        assert len(pt) == 2


def test_polar_intercepts_on_arc(polar):
    r = polar._radii()[0]
    pts = polar._intercepts(r)
    L = polar.polargraph.ell / 2
    for x, y in pts:
        assert np.hypot(x + L, y) == pytest.approx(r, rel=1e-6)


def test_polar_vertices_shape(polar):
    v = polar.vertices()
    assert v.ndim == 2
    assert v.shape[1] == 2


def test_polar_vertices_count(polar):
    v = polar.vertices()
    n_arcs = len(polar._radii())
    assert v.shape[0] == 2 * n_arcs


def test_polar_trajectory_lengths_match(polar):
    x, y = polar.trajectory()
    assert len(x) == len(y)
    assert len(x) > 0


# --- TarzanScan ---

def test_tarzan_x0_default():
    t = TarzanScan()
    assert t.x0 == 0.0


def test_tarzan_x0_setter(tarzan):
    tarzan.x0 = 0.1
    assert tarzan.x0 == pytest.approx(0.1)


def test_tarzan_cycle_returns_four_points(tarzan):
    _, y_top, _, _ = tarzan.rect()
    p0 = np.array([tarzan.x0, y_top])
    result = tarzan._cycle(p0)
    assert result is not None
    assert len(result) == 4
    for pt in result:
        assert pt.shape == (2,)


def test_tarzan_cycle_p1_on_right_edge(tarzan):
    _, y_top, x_right, _ = tarzan.rect()
    p0 = np.array([tarzan.x0, y_top])
    p1, _, _, _ = tarzan._cycle(p0)
    assert p1[0] == pytest.approx(x_right, abs=1e-9)


def test_tarzan_cycle_p2_on_bottom_edge(tarzan):
    _, y_top, _, y_bottom = tarzan.rect()
    p0 = np.array([tarzan.x0, y_top])
    _, p2, _, _ = tarzan._cycle(p0)
    assert p2[1] == pytest.approx(y_bottom, abs=1e-9)


def test_tarzan_cycle_p3_on_left_edge(tarzan):
    x_left, y_top, _, _ = tarzan.rect()
    p0 = np.array([tarzan.x0, y_top])
    _, _, p3, _ = tarzan._cycle(p0)
    assert p3[0] == pytest.approx(x_left, abs=1e-9)


def test_tarzan_cycle_p4_on_top_edge(tarzan):
    _, y_top, _, _ = tarzan.rect()
    p0 = np.array([tarzan.x0, y_top])
    _, _, _, p4 = tarzan._cycle(p0)
    assert p4[1] == pytest.approx(y_top, abs=1e-9)


def test_tarzan_cycle_p1_on_arc_around_right_pulley(tarzan):
    '''P0 and P1 must be equidistant from the right pulley.'''
    _, y_top, _, _ = tarzan.rect()
    L, R = tarzan._pulley_positions()
    p0 = np.array([tarzan.x0, y_top])
    p1, _, _, _ = tarzan._cycle(p0)
    assert np.linalg.norm(p0 - R) == pytest.approx(np.linalg.norm(p1 - R), rel=1e-9)


def test_tarzan_cycle_p2_on_arc_around_left_pulley(tarzan):
    '''P1 and P2 must be equidistant from the left pulley.'''
    _, y_top, _, _ = tarzan.rect()
    L, R = tarzan._pulley_positions()
    p0 = np.array([tarzan.x0, y_top])
    p1, p2, _, _ = tarzan._cycle(p0)
    assert np.linalg.norm(p1 - L) == pytest.approx(np.linalg.norm(p2 - L), rel=1e-9)


def test_tarzan_cycle_all_points_have_positive_y(tarzan):
    '''All four cycle corners must be physically below the motors (y > 0).'''
    _, y_top, _, _ = tarzan.rect()
    p0 = np.array([tarzan.x0, y_top])
    p1, p2, p3, p4 = tarzan._cycle(p0)
    for pt in [p1, p2, p3, p4]:
        assert pt[1] > 0


def test_tarzan_vertices_shape(tarzan):
    v = tarzan.vertices()
    assert v.ndim == 2
    assert v.shape[1] == 2


def test_tarzan_vertices_minimum_length(tarzan):
    '''At least one full cycle (5 points: start + 4 corners).'''
    v = tarzan.vertices()
    assert v.shape[0] >= 5


def test_tarzan_vertices_start_on_top_edge(tarzan):
    _, y_top, _, _ = tarzan.rect()
    v = tarzan.vertices()
    assert v[0, 1] == pytest.approx(y_top, abs=1e-9)
    assert v[0, 0] == pytest.approx(tarzan.x0)


def test_tarzan_vertices_count_multiple_of_four_plus_one(tarzan):
    '''Vertex count must be 4*n_cycles + 1 (start point + 4 per cycle).'''
    v = tarzan.vertices()
    assert (v.shape[0] - 1) % 4 == 0


def test_tarzan_trajectory_shape(tarzan):
    t = tarzan.trajectory()
    assert t.ndim == 2
    assert t.shape[0] == 2


def test_tarzan_trajectory_more_points_than_vertices(tarzan):
    v = tarzan.vertices()
    t = tarzan.trajectory()
    assert t.shape[1] > v.shape[0]


def test_tarzan_trajectory_starts_at_first_vertex(tarzan):
    v = tarzan.vertices()
    t = tarzan.trajectory()
    assert t[0, 0] == pytest.approx(v[0, 0], abs=1e-9)
    assert t[1, 0] == pytest.approx(v[0, 1], abs=1e-9)


def test_tarzan_trajectory_first_arc_constant_radius(tarzan):
    '''All points on the first arc must be equidistant from the right pulley.'''
    _, R = tarzan._pulley_positions()
    t = tarzan.trajectory()
    n = tarzan._TRAJECTORY_PTS
    xs, ys = t[0, :n], t[1, :n]
    radii = np.hypot(xs - R[0], ys - R[1])
    assert radii == pytest.approx(radii[0], rel=1e-6)


def test_tarzan_cycle_returns_none_when_geometry_invalid(tarzan):
    '''_cycle returns None when belt length is shorter than edge distance.'''
    # Place start very close to the right pulley so the belt length is
    # shorter than the horizontal distance from R to x_right.
    _, R = tarzan._pulley_positions()
    p_near = R + np.array([0.001, 0.001])  # tiny belt length
    assert tarzan._cycle(p_near) is None


# --- home / center ---

def test_home_moves_to_home_x(scan):
    scan.home()
    x, _, _ = scan.polargraph.position
    assert x == pytest.approx(0.0)


def test_home_moves_to_home_y(scan):
    scan.home()
    _, y, _ = scan.polargraph.position
    assert y == pytest.approx(scan.polargraph.y0)


def test_center_moves_to_dx(scan):
    scan.center()
    x, _, _ = scan.polargraph.position
    assert x == pytest.approx(scan.dx)


def test_center_moves_to_scan_midpoint(scan):
    scan.center()
    _, y, _ = scan.polargraph.position
    expected = scan.polargraph.y0 + scan.dy + scan.height / 2.
    assert y == pytest.approx(expected, abs=scan.polargraph.ds)


# --- moveTo return value / interrupt ---

def test_moveto_returns_true_on_completion(scan):
    assert scan.moveTo([[0.1, 0.3]]) is True


def test_interrupt_causes_moveto_to_return_false(scan):
    scan.interrupt()
    assert scan.moveTo([[0.1, 0.3]]) is False


def test_interrupt_resets_after_moveto(scan):
    scan.interrupt()
    scan.moveTo([[0.1, 0.3]])
    assert scan.moveTo([[0.0, 0.2]]) is True


# --- scan / scanning ---

def test_not_scanning_before_scan(scan):
    assert not scan.scanning()


def test_scan_emits_scan_finished(scan, qtbot):
    with qtbot.waitSignal(scan.scanFinished, timeout=5000):
        scan.scan()


def test_scan_emits_data_ready(scan, qtbot):
    received = []
    scan.dataReady.connect(received.append)
    scan.scan()
    assert len(received) > 0


def test_scan_returns_home_after_completion(scan):
    scan.scan()
    x, y, _ = scan.polargraph.position
    assert x == pytest.approx(0.0)
    assert y == pytest.approx(scan.polargraph.y0)
