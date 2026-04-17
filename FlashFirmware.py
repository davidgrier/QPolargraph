'''FlashFirmware — Arduino firmware installer for QPolargraph.

Detects attached Arduino boards via ``QSerialPortInfo``, installs any
missing Arduino libraries, and flashes the bundled ``acam3`` firmware
using ``arduino-cli``.

Requires ``arduino-cli`` to be installed and on ``PATH``.  See
https://arduino.github.io/arduino-cli/ for installation instructions.

Flash sequence
--------------
When the user clicks *Flash Firmware*, the following steps run in order
in a background thread:

1. **Check libraries** — compares ``ARDUINO_LIBS`` against the output of
   ``arduino-cli lib list``.  Any missing libraries are installed
   automatically via ``arduino-cli lib install``.
2. **Compile** — ``arduino-cli compile --fqbn <fqbn> hardware/arduino/acam3/``
3. **Upload** — ``arduino-cli upload --fqbn <fqbn> --port <port> hardware/arduino/acam3/``

Each step streams its output to the dialog's text area in real time.
The flash button is re-enabled on completion, and a ``QMessageBox``
reports success or failure.

Standalone usage
----------------
Run directly from the command line::

    qpolargraph-flash

or::

    python -m QPolargraph.FlashFirmware

Integration into a QMainWindow application
-------------------------------------------
``FlashDialog`` is a standard ``QDialog`` and can be wired to a menu
action in any ``QMainWindow`` subclass::

    from QPolargraph.FlashFirmware import FlashDialog

    flash_action = QtWidgets.QAction('Flash Arduino Firmware...', self)
    flash_action.triggered.connect(lambda: FlashDialog(self).exec())
    tools_menu.addAction(flash_action)

Passing ``self`` as the parent centres the dialog over the application
window.  The import can be deferred to the slot so that ``FlashFirmware``
is only loaded when the user triggers the action.
'''

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

from qtpy import QtCore, QtWidgets
from qtpy.QtSerialPort import QSerialPortInfo


ARDUINO_VIDS = {
    0x2341,  # Arduino LLC (official boards)
    0x2A03,  # Arduino SRL
    0x1A86,  # QinHeng CH340 (common clones)
    0x0403,  # FTDI (some clones)
}

SKETCH = Path(__file__).parent / 'hardware' / 'arduino' / 'acam3'
DEFAULT_FQBN = 'arduino:avr:uno'
ARDUINO_LIBS = [
    'Adafruit Motor Shield V2 Library',
    'AccelStepper',
]


def _firmware_version() -> str:
    ino = SKETCH / 'acam3.ino'
    pattern = re.compile(r'#define\s+VERSION\s+"acam(\S+)"')
    with ino.open() as f:
        for line in f:
            if m := pattern.match(line.strip()):
                return m.group(1)
    raise RuntimeError('VERSION not found in acam3.ino')


def find_arduinos() -> list[QSerialPortInfo]:
    '''Return serial ports whose USB vendor ID matches a known Arduino VID.'''
    return [p for p in QSerialPortInfo.availablePorts()
            if p.vendorIdentifier() in ARDUINO_VIDS]


def detect_fqbn(port_name: str) -> str:
    '''Ask arduino-cli for the board FQBN; fall back to DEFAULT_FQBN.'''
    try:
        result = subprocess.run(
            ['arduino-cli', 'board', 'list', '--format', 'json'],
            capture_output=True, text=True, timeout=10
        )
        data = json.loads(result.stdout)
        # arduino-cli v1 wraps output in {'detected_ports': [...]}
        ports = (data.get('detected_ports', [])
                 if isinstance(data, dict) else data)
        for entry in ports:
            address = entry.get('port', {}).get('address', '')
            if address == port_name:
                matching = entry.get('matching_boards', [])
                if matching:
                    return matching[0].get('fqbn', DEFAULT_FQBN)
    except Exception:
        pass
    return DEFAULT_FQBN


class _FlashWorker(QtCore.QThread):
    '''Background thread that installs libraries, compiles, and uploads acam3.

    Runs three steps in sequence: library check/install, ``arduino-cli
    compile``, and ``arduino-cli upload``.  Progress is streamed line by
    line via the ``output`` signal.  The ``finished`` signal carries
    ``True`` on success and ``False`` on any failure.
    '''

    output = QtCore.Signal(str)
    finished = QtCore.Signal(bool)

    def __init__(self, port: str, fqbn: str, parent=None):
        super().__init__(parent)
        self._port = port
        self._fqbn = fqbn

    def _run(self, *args, timeout: int = 120) -> bool:
        '''Run a subprocess; emit its output; return True on success.'''
        try:
            result = subprocess.run(
                args, capture_output=True, text=True, timeout=timeout
            )
        except FileNotFoundError:
            self.output.emit(
                'arduino-cli not found.\n'
                'Install it from https://arduino.github.io/arduino-cli/'
            )
            return False
        except subprocess.TimeoutExpired:
            self.output.emit('Operation timed out.')
            return False
        for line in (result.stdout + result.stderr).splitlines():
            if line.strip():
                self.output.emit(line)
        return result.returncode == 0

    def _installed_libraries(self) -> set[str]:
        '''Return the names of currently installed arduino-cli libraries.'''
        try:
            result = subprocess.run(
                ['arduino-cli', 'lib', 'list', '--format', 'json'],
                capture_output=True, text=True, timeout=30
            )
            data = json.loads(result.stdout)
            libs = (data.get('installed_libraries', [])
                    if isinstance(data, dict) else data)
            return {entry['library']['name'] for entry in libs}
        except Exception:
            return set()

    def _ensure_libraries(self) -> bool:
        '''Install missing and upgrade outdated Arduino libraries.'''
        self.output.emit('Checking Arduino libraries...')
        installed = self._installed_libraries()
        missing = [lib for lib in ARDUINO_LIBS if lib not in installed]
        for lib in missing:
            self.output.emit(f'Installing {lib}...')
            if not self._run('arduino-cli', 'lib', 'install', lib, timeout=60):
                return False
        present = [lib for lib in ARDUINO_LIBS if lib in installed]
        for lib in present:
            self.output.emit(f'Updating {lib}...')
            self._run('arduino-cli', 'lib', 'upgrade', lib, timeout=60)
        if not missing:
            self.output.emit('All required libraries are up to date.')
        return True

    def run(self) -> None:
        if not self._ensure_libraries():
            self.finished.emit(False)
            return

        self.output.emit(f'Compiling for {self._fqbn}...')
        ok = self._run('arduino-cli', 'compile',
                       '--fqbn', self._fqbn, str(SKETCH))
        if not ok:
            self.finished.emit(False)
            return

        self.output.emit(f'Uploading to {self._port}...')
        ok = self._run('arduino-cli', 'upload',
                       '--fqbn', self._fqbn,
                       '--port', self._port,
                       str(SKETCH), timeout=60)
        if not ok:
            self.finished.emit(False)
            return

        self.output.emit('Firmware installed successfully.')
        self.finished.emit(True)


class FlashDialog(QtWidgets.QDialog):
    '''Dialog to detect an attached Arduino and flash the acam3 firmware.

    Enumerates serial ports using ``QSerialPortInfo``, filters by known
    Arduino USB vendor IDs, and delegates the three-step flash sequence
    (library install, compile, upload) to a background
    :class:`_FlashWorker` thread.  Requires ``arduino-cli`` to be
    installed and on ``PATH``.

    Parameters
    ----------
    parent : QtWidgets.QWidget, optional
        Parent widget.
    '''

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle('Flash acam3 Firmware')
        self._worker: _FlashWorker | None = None
        self._setup_ui()
        self._populate()

    def _setup_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)

        form = QtWidgets.QFormLayout()
        self._port_combo = QtWidgets.QComboBox()
        try:
            version = _firmware_version()
            label = f'acam3 v{version}'
        except RuntimeError:
            label = 'acam3'
        form.addRow('Firmware:', QtWidgets.QLabel(label))
        form.addRow('Arduino:', self._port_combo)
        layout.addLayout(form)

        self._output = QtWidgets.QPlainTextEdit()
        self._output.setReadOnly(True)
        self._output.setMinimumSize(520, 160)
        layout.addWidget(self._output)

        buttons = QtWidgets.QDialogButtonBox()
        self._flash_btn = buttons.addButton(
            'Flash Firmware',
            QtWidgets.QDialogButtonBox.ButtonRole.ActionRole
        )
        close_btn = buttons.addButton(
            QtWidgets.QDialogButtonBox.StandardButton.Close
        )
        self._flash_btn.clicked.connect(self._flash)
        close_btn.clicked.connect(self.reject)
        layout.addWidget(buttons)

    def _populate(self) -> None:
        arduinos = find_arduinos()
        if not arduinos:
            self._output.appendPlainText('No Arduino detected.')
            self._flash_btn.setEnabled(False)
            return
        for port in arduinos:
            desc = port.description() or 'Unknown board'
            self._port_combo.addItem(
                f'{port.portName()} — {desc}',
                userData=port.systemLocation()
            )

    def _flash(self) -> None:
        port = self._port_combo.currentData()
        if not port:
            return
        self._flash_btn.setEnabled(False)
        self._output.clear()
        display = self._port_combo.currentText().split(' — ')[0]
        self._output.appendPlainText(f'Detecting board on {display}...')
        fqbn = detect_fqbn(port)
        self._output.appendPlainText(f'Board: {fqbn}')
        self._worker = _FlashWorker(port, fqbn, self)
        self._worker.output.connect(self._output.appendPlainText)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    def _on_finished(self, success: bool) -> None:
        self._flash_btn.setEnabled(True)
        if success:
            QtWidgets.QMessageBox.information(
                self, 'Done', 'Firmware flashed successfully.'
            )
        else:
            QtWidgets.QMessageBox.warning(
                self, 'Failed',
                'Firmware installation failed.\nSee output for details.'
            )


def main() -> None:
    '''Entry point for the ``qpolargraph-flash`` GUI script.'''
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    dialog = FlashDialog()
    dialog.exec()


if __name__ == '__main__':
    main()
