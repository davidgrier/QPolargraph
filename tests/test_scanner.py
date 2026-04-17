import numpy as np
import pytest
from QPolargraph.QScanner import QScanner
from QPolargraph.hardware.fake import FakePolargraph
from QPolargraph.patterns.PolarScan import PolarScan
from QPolargraph.patterns.RasterScan import RasterScan


@pytest.fixture
def scanner(qtbot, tmp_path):
    w = QScanner(configdir=str(tmp_path / 'config'))
    qtbot.addWidget(w)
    return w


@pytest.fixture
def fake_scanner(qtbot, tmp_path):
    w = QScanner(fake=True, configdir=str(tmp_path / 'config'))
    w.scanner.pattern.polargraph.step_delay = 0.
    qtbot.addWidget(w)
    return w


# --- construction ---

def test_scanner_creates(scanner):
    assert scanner is not None


def test_scanner_has_polargraph_attribute(scanner):
    assert hasattr(scanner, 'polargraph')


def test_scanner_has_scanner_attribute(scanner):
    assert hasattr(scanner, 'scanner')


def test_default_scan_pattern_type(scanner):
    assert isinstance(scanner.scanner.pattern, PolarScan)


def test_scan_button_initial_text(scanner):
    assert scanner.scan.text() == 'Scan'


def test_not_scanning_initially(scanner):
    assert not scanner.scanner.pattern.scanning()


# --- SCAN_PATTERN class attribute ---

def test_scan_pattern_override():
    class RasterScanner(QScanner):
        SCAN_PATTERN = RasterScan
    assert RasterScanner.SCAN_PATTERN is RasterScan


# --- status bar ---

def test_show_status(scanner):
    scanner.showStatus('hello')
    assert scanner.statusBar().currentMessage() == 'hello'


# --- signals ---

def test_data_ready_signal(scanner, qtbot):
    received = []
    scanner.dataReady.connect(received.append)
    scanner._onDataReady(np.array([0.1, 0.2]))
    assert len(received) == 1
    assert received[0] == {'x': pytest.approx(0.1), 'y': pytest.approx(0.2)}


def test_update_plot_does_not_raise(scanner):
    scanner.updatePlot()


# --- plotData ---

def test_plot_data_scalar(scanner):
    scanner.plotData(0.1, 0.2, 0.5)


def test_plot_data_array(scanner):
    x = np.linspace(-0.1, 0.1, 5)
    y = np.linspace(0.2, 0.4, 5)
    hue = np.linspace(0.0, 1.0, 5)
    scanner.plotData(x, y, hue)


# --- settings ---

def test_save_restore_settings(scanner):
    scanner.saveSettings()
    scanner.restoreSettings()


def test_save_sets_status(scanner):
    scanner.saveSettings()
    assert 'saved' in scanner.statusBar().currentMessage().lower()


def test_restore_sets_status(scanner):
    scanner.restoreSettings()
    assert 'restored' in scanner.statusBar().currentMessage().lower()


# --- fake=True constructor ---

def test_fake_scanner_uses_fake_polargraph(fake_scanner):
    assert isinstance(fake_scanner.polargraph.device, FakePolargraph)


# --- scan lifecycle ---

def test_scan_started_changes_button_text(fake_scanner, qtbot):
    fake_scanner.scanStarted()
    assert fake_scanner.scan.text() == 'Stop'
    qtbot.waitUntil(lambda: fake_scanner.scan.text() == 'Scan', timeout=5000)


def test_scan_controls_disabled_while_scanning(fake_scanner, qtbot):
    fake_scanner.scanStarted()
    assert not fake_scanner.center.isEnabled()
    qtbot.waitUntil(lambda: fake_scanner.center.isEnabled(), timeout=5000)


def test_scan_finished_restores_button(fake_scanner, qtbot):
    fake_scanner.scanStarted()
    qtbot.waitUntil(lambda: fake_scanner.scan.text() == 'Scan', timeout=5000)


def test_scan_finished_restores_controls(fake_scanner, qtbot):
    fake_scanner.scanStarted()
    qtbot.waitUntil(lambda: fake_scanner.center.isEnabled(), timeout=5000)
    assert fake_scanner.home.isEnabled()
    assert fake_scanner.polargraph.isEnabled()
    assert fake_scanner.scanner.isEnabled()


def test_scan_finished_shows_status(fake_scanner, qtbot):
    fake_scanner.scanStarted()
    qtbot.waitUntil(
        lambda: 'complete' in fake_scanner.statusBar().currentMessage().lower(),
        timeout=5000)


def test_scan_aborted_sets_button_text(fake_scanner, qtbot):
    fake_scanner.scanStarted()
    fake_scanner.scanAborted()
    assert fake_scanner.scan.text() == 'Stopping'
    qtbot.waitUntil(lambda: fake_scanner.scan.text() == 'Scan', timeout=5000)


# --- _startMove (Home / Center) ---

def test_home_disables_controls(fake_scanner, qtbot):
    fake_scanner._startMove(fake_scanner.scanner.pattern.home)
    assert not fake_scanner.center.isEnabled()
    qtbot.waitUntil(lambda: fake_scanner.center.isEnabled(), timeout=5000)


def test_center_disables_controls(fake_scanner, qtbot):
    fake_scanner._startMove(fake_scanner.scanner.pattern.center)
    assert not fake_scanner.home.isEnabled()
    qtbot.waitUntil(lambda: fake_scanner.home.isEnabled(), timeout=5000)
