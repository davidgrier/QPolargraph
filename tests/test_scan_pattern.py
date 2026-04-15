import numpy as np
import pytest
from QPolargraph.fake import FakePolargraph
from QPolargraph.QScanPattern import QScanPattern
from QPolargraph.RasterScan import RasterScan
from QPolargraph.PolarScan import PolarScan


@pytest.fixture
def pg():
    return FakePolargraph()


@pytest.fixture
def scan(pg):
    return QScanPattern(polargraph=pg)


@pytest.fixture
def raster(pg):
    return RasterScan(polargraph=pg)


@pytest.fixture
def polar(pg):
    return PolarScan(polargraph=pg)


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
    assert t.shape[1] == 2


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


def test_raster_trajectory_matches_vertices(raster):
    v = raster.vertices()
    t = raster.trajectory()
    assert t.shape[1] == v.shape[0]


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
