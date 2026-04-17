# QPolargraph

[![Tests](https://github.com/davidgrier/QPolargraph/actions/workflows/tests.yml/badge.svg)](https://github.com/davidgrier/QPolargraph/actions/workflows/tests.yml)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)

A Qt-based instrument interface for a two-dimensional polargraph scanner.
Built on [QInstrument](https://github.com/davidgrier/QInstrument).

A [polargraph](http://www.polargraph.co.uk/) translates a payload to any
position within its scan area using two stepper motors and a timing belt.
[Originally developed](http://juerglehni.com/works/hektor) by Jürg Lehni and
Uli Franke as a drawing machine, the design scales easily to large areas,
delivers millimeter-scale positioning accuracy, and is very cost-effective to
build.

<img src="docs/QScanner.png" width="75%" alt="QScanner interface">

## Hardware

| Component | Description |
|-----------|-------------|
| 2× Nema-17 stepper motor | Mounted above and to either side of the scan area |
| GT2 timing belt | Spans both motors; payload hangs from its midpoint |
| GT2 drive gear (25-tooth) | One per motor; engages the belt |
| [Adafruit Motor Shield v2](https://www.adafruit.com/product/1438) | Drives both steppers from a single Arduino |
| Arduino (Uno or compatible) | Runs the `acam3` firmware; connects to the host via USB |

The belt forms a V-shape between the two motors. Each motor changes the length
of one side of the V, moving the payload in two dimensions.

## Firmware

Load `arduino/acam3/acam3.ino` onto the Arduino using the
[Arduino IDE](https://www.arduino.cc/en/software) before first use.

The Python package version and the firmware version are coupled: `Motors`
checks that the connected Arduino reports firmware version
`Motors.FIRMWARE_VERSION` during `identify()` and refuses to open the
port if they do not match.

## Installation

Clone the repository and install in editable mode:

```bash
git clone https://github.com/davidgrier/QPolargraph
cd QPolargraph
python -m venv .qp
source .qp/bin/activate          # Windows: .qp\Scripts\activate
pip install -e ".[dev]"
pip install PyQt6                # or PyQt5, PySide2, PySide6
```

[QInstrument](https://github.com/davidgrier/QInstrument) is installed
automatically as a dependency.

## Calibration

Five geometric parameters describe the polargraph. Set them in the
`QPolargraphWidget` control panel or pass them directly to `Polargraph()`:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `ell` | 1.0 m | Horizontal distance between the two motor pulley centres |
| `y0` | 0.1 m | Vertical distance from the pulleys to the home position |
| `pitch` | 2.0 mm | GT2 belt tooth pitch |
| `circumference` | 25 | Number of belt teeth on the drive gear |
| `steps` | 200 | Motor steps per revolution |

Measure `ell` and `y0` with a ruler after mounting the motors.
`pitch`, `circumference`, and `steps` are determined by the belt and gear
specifications and normally do not need to change.

Settings are saved to `~/.QScanner/` automatically when the application
closes, so calibration only needs to be done once.

## Quick start

### Scanner application

```bash
python -m QPolargraph
# or, after installation:
qpolargraph
```

The application opens a live plot showing the belt geometry and the scan
trajectory. Use the **Scan** button to start a polar-arc sweep, or
**Home** / **Center** to move the payload to the home or centre position.

### Embedding in your own application

Subclass `QScanner` to add experiment-specific data acquisition:

```python
from qtpy.QtWidgets import QApplication
from qtpy import QtCore
from QPolargraph.QScanner import QScanner
import sys


class MyScanner(QScanner):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scanner.dataReady.connect(self.acquire)

    @QtCore.Slot(object)
    def acquire(self, position):
        x, y = position
        # measure something at (x, y) and call self.plotData(x, y, hue)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    scanner = MyScanner()
    scanner.show()
    sys.exit(app.exec())
```

### Controlling the hardware directly

```python
from qtpy.QtCore import QCoreApplication
from QPolargraph.Polargraph import Polargraph
import sys

app = QCoreApplication(sys.argv)
pg = Polargraph(ell=0.8, y0=0.15).find()   # auto-detects USB port
print(pg.position)                           # (x, y, running) in metres
pg.moveTo(0.0, 0.3)
while pg.running():
    pass
pg.release()
```

## Architecture

```
QInstrument.QSerialInstrument
└── Motors               # acam3 serial protocol: goto, speed, position, …
    └── Polargraph       # geometry: step indexes ↔ Cartesian coordinates

QInstrument.QInstrumentWidget
└── QRasterScanWidget    # scan-pattern parameter controls

QInstrument.QInstrumentWidget
└── QPolargraphWidget    # polargraph hardware controls

QtCore.QObject
└── QScanPattern         # base: rectangular perimeter trajectory
    ├── RasterScan       # row-by-row zigzag raster
    └── PolarScan        # arc-by-arc sweep centred on the left pulley

QtWidgets.QMainWindow
└── QScanner             # full application: live plot + scan controls
```

## Development

Run the test suite:

```bash
source .qp/bin/activate
pytest tests/
```

Tests run automatically before every `git push`. To install the pre-push
hook in a fresh clone:

```bash
git config core.hooksPath .githooks
```

## Acknowledgements

Work on this project at New York University is supported by the
National Science Foundation of the United States under award number DMR-2104837.

## References

H. W. Gao, K. I. Mishra, A. Winters, S. Wolin, and D. G. Grier,
"Flexible wide-field high-resolution scanning camera for continuous-wave acoustic holography,"
*Review of Scientific Instruments* **89**, 114901 (2018).
https://doi.org/10.1063/1.5053666
