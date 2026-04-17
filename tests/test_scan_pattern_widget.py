import pytest
from QPolargraph.patterns.QScanPatternWidget import QScanPatternWidget
from QPolargraph.patterns.RasterScan import RasterScan
from QPolargraph.patterns.PolarScan import PolarScan


@pytest.fixture
def widget(qtbot):
    w = QScanPatternWidget()
    qtbot.addWidget(w)
    return w


def test_default_pattern_type(widget):
    assert isinstance(widget.pattern, PolarScan)


def test_spinboxes_initialized_from_pattern(widget):
    for name in ('width', 'height', 'dx', 'dy', 'step'):
        assert getattr(widget, name).value() == pytest.approx(
            getattr(widget.pattern, name))


def test_set_pattern_syncs_spinboxes(widget):
    raster = RasterScan()
    raster.width = 0.3
    widget.pattern = raster
    assert widget.width.value() == pytest.approx(0.3)
    assert isinstance(widget.pattern, RasterScan)


def test_spinbox_change_updates_pattern(widget):
    original = widget.pattern.width
    new_value = original + 0.05
    widget.width.setValue(new_value)
    assert widget.pattern.width == pytest.approx(new_value)


def test_pattern_changed_signal_emitted(widget, qtbot):
    with qtbot.waitSignal(widget.patternChanged, timeout=1000):
        widget.width.setValue(widget.width.value() + 0.05)


def test_settings_getter_returns_all_keys(widget):
    s = widget.settings
    for name in ('width', 'height', 'dx', 'dy', 'step'):
        assert name in s


def test_settings_getter_matches_pattern(widget):
    s = widget.settings
    for name in ('width', 'height', 'dx', 'dy', 'step'):
        assert s[name] == pytest.approx(getattr(widget.pattern, name))


def test_settings_setter_updates_spinboxes_and_pattern(widget):
    new_settings = {'width': 0.2, 'height': 0.3, 'dx': 0.01, 'dy': 0.01, 'step': 1.0}
    widget.settings = new_settings
    for name, value in new_settings.items():
        assert getattr(widget, name).value() == pytest.approx(value)
        assert getattr(widget.pattern, name) == pytest.approx(value)


def test_settings_setter_ignores_unknown_keys(widget):
    widget.settings = {'unknown_key': 99.0}  # should not raise
