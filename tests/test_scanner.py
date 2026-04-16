import numpy as np
import pytest
from QPolargraph.QScanner import QScanner
from QPolargraph.PolarScan import PolarScan
from QPolargraph.RasterScan import RasterScan


@pytest.fixture
def scanner(qtbot, tmp_path):
    w = QScanner(configdir=str(tmp_path / 'config'))
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
