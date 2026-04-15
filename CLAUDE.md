# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

QPolargraph is a Qt-based instrument interface for a two-dimensional polargraph scanner. A polargraph uses two stepper motors and a GT2 timing belt to position a payload anywhere within its scan area. The motors are driven by an Arduino microcontroller (running the `acam3` firmware) connected to the host computer via USB serial. This package provides both the low-level hardware abstraction and a GUI application framework, built on top of [QInstrument](https://github.com/davidgrier/QInstrument).

QPolargraph is a companion project to QInstrument and should adopt the same coding standards, project structure, Qt binding conventions, and style practices as QInstrument.

## Development Commands

The virtual environment should live in `.qp/` (mirroring QInstrument's `.qi/` convention):
```bash
python -m venv .qp
source .qp/bin/activate
pip install -e ".[dev]"
```

Run the scanner application:
```bash
python -m QPolargraph
```

Run tests:
```bash
pytest tests/
```

Git hooks live in `.githooks/` (tracked). Activate them once per clone:
```bash
git config core.hooksPath .githooks
```
The `pre-push` hook runs the full test suite and blocks the push on failure.

## Architecture

### Class Hierarchy

```
QInstrument.lib.QSerialInstrument
└── Motors                   # Serial communication with Arduino (acam3 protocol)
    └── Polargraph           # Geometry: motor step indexes ↔ Cartesian coordinates

QInstrument.lib.QInstrumentWidget
└── QRasterScanWidget        # Widget for raster scan pattern controls

QInstrument.lib.QInstrumentWidget
└── QPolargraphWidget        # Widget for polargraph hardware controls

QtCore.QObject
└── QScanPattern             # Base class for scan trajectory patterns
    ├── RasterScan            # Raster (row-by-row) scan pattern
    └── PolarScan             # Polar (arc-by-arc) scan pattern

QtWidgets.QMainWindow
└── QScanner                 # Application framework: scanner GUI with live plot
```

### Key Classes

**`Motors`** — Inherits `QSerialInstrument`. Communicates with the Arduino over USB serial using the `acam3` protocol. Defines a `comm` (serial settings) class attribute. Implements `identify()` (checks firmware version string), and provides properties `indexes` (current step counts), `motor_speed`, and `acceleration`, plus methods `goto(n1, n2)`, `home()`, `stop()`, `release()`, and `running()`.

**`Polargraph`** — Inherits `Motors`. Adds geometry: converts between motor step-index space and Cartesian coordinates in metres. Properties include `ell` (motor separation), `y0` (home vertical offset), `pitch`, `circumference`, `steps` (belt/gear parameters), `ds` (distance per step), `s0` (belt length at home), and `position` (current Cartesian coordinates). Method `moveTo(x, y)` coordinates both motors to reach a target position, adjusting speeds so both arrive simultaneously.

**`QScanPattern`** — `QObject` subclass with a `PropertyMeta` metaclass that wires `Property` descriptors to `pyqtProperty`. Manages the scan geometry (`width`, `height`, `dx`, `dy`, `step`) and drives the polargraph through a scan via `moveTo()`. Base implementation provides a rectangular perimeter trajectory. Subclasses override `vertices()` and `trajectory()`.

**`RasterScan`** — Overrides `vertices()` to produce a row-by-row zigzag raster across the scan rectangle. Step size is in mm.

**`PolarScan`** — Overrides `vertices()` to produce arc-by-arc sweeps centred on the left motor pulley.

**`QPolargraphWidget`** — Thin wrapper: instantiates a `Polargraph`, passes it and `PolargraphWidget.ui` to `QThreadedInstrumentWidget`.

**`QRasterScanWidget`** — Thin wrapper: instantiates a `PolarScan` (default) and passes it and `RasterScanWidget.ui` to `QInstrumentWidget`.

**`QScanner`** — `QMainWindow` application framework. Loads `Scanner.ui`, wires up a `QPolargraphWidget` and a `QRasterScanWidget` (from the `.ui` file), uses `pyqtgraph` for live trajectory and position display, and provides `scan`/`stop`/`home`/`center` controls. Intended to be subclassed for experiment-specific applications.

### Arduino Firmware

The Arduino sketch lives in `arduino/acam3/acam3.ino`. The host-side `Motors.identify()` checks that the firmware reports `acam{version}` where the version matches `Motors.__version__`. The serial protocol uses single-character command codes (`Q` query version, `G` goto, `P` position, `V` speed, `A` acceleration, `S` stop, `X` release, `R` running).

## Migration Goals

QPolargraph is being brought up to QInstrument's standards. Work to be done:

- **License**: Change from MIT to GPL v3 (consistent with QInstrument).
- **Package config**: Add `pyproject.toml`; remove `requirements.txt`.
- **Qt binding**: Replace all `PyQt5` imports with `qtpy`; replace `pyqtSignal`/`pyqtSlot`/`pyqtProperty` with `QtCore.Signal`/`QtCore.Slot`/`QtCore.Property`.
- **`comm` dict**: Replace short-form enum access (`QSerialInstrument.Baud9600`) with long-form (`QSerialInstrument.BaudRate.Baud9600`); rename `settings` → `comm` in `Motors`.
- **Property system**: Migrate `Polargraph` properties from the local `Property()`/`pyqtProperty` pattern to `QInstrument`'s `registerProperty()` API. Migrate `QScanPattern` from `PropertyMeta`/`Property` to `registerProperty()`.
- **Imports**: Convert `__init__.py` to lazy imports (matching QInstrument's `lib/__init__.py` pattern).
- **Type hints**: Add throughout (Python 3.10+ union syntax `str | None`).
- **Docstrings**: Upgrade to NumPy style with ReST cross-references; remove `Inherits` sections; add units in property descriptions.
- **Tests**: Create `tests/` with a pytest suite (use `pytest-qt` for Qt testing).
- **Docs**: Add Sphinx documentation under `docs/`; add `.readthedocs.yaml`.
- **CI/CD**: Add `.github/workflows/tests.yml` and `.github/workflows/publish.yml`.
- **Git hooks**: Add `.githooks/pre-push` that runs `pytest tests/` before push.
- **Entry point**: Add `__main__.py` and register `qpolargraph` as a GUI script in `pyproject.toml`.
- **CHANGELOG**: Add `CHANGELOG.rst`.

## Coding Conventions

Follow QInstrument conventions throughout:

### Qt Imports

**Always import Qt via `qtpy`**, never directly from PyQt5/PyQt6:
```python
from qtpy import QtCore, QtWidgets
```
Use `QtCore.Signal`, `QtCore.Slot`, `QtCore.Property` — not `pyqtSignal`, `pyqtSlot`, `pyqtProperty`.

### Serial Settings

Define `comm` as a class attribute using long-form scoped enum access:
```python
comm = dict(baudRate=QSerialInstrument.BaudRate.Baud9600,
            dataBits=QSerialInstrument.DataBits.Data8,
            stopBits=QSerialInstrument.StopBits.OneStop,
            parity=QSerialInstrument.Parity.NoParity,
            flowControl=QSerialInstrument.FlowControl.NoFlowControl,
            eol='\n')

def __init__(self, portName=None, **kwargs):
    super().__init__(portName, **(self.comm | kwargs))
```

### Imports from QInstrument

Always import by full module path:
```python
from QInstrument.lib.QSerialInstrument import QSerialInstrument
from QInstrument.lib.QInstrumentWidget import QInstrumentWidget
```

### Docstrings

- NumPy style throughout.
- No `Inherits` section (redundant with the class signature).
- Units in brackets after the property name, e.g. `ell : float` followed by `Motor separation [m]`.
- `identify()` always gets a docstring explaining what response it checks for.
- Methods: use `Parameters` (not `Arguments`).

### Type Hints

Add to all new and migrated code. Use `str | None` union syntax (Python 3.10+). Use `numpy.typing.ArrayLike` for array parameters.

### Version

Package version is defined in `pyproject.toml` and accessed via:
```python
from importlib.metadata import version, PackageNotFoundError
try:
    __version__ = version('QPolargraph')
except PackageNotFoundError:
    __version__ = None
```
The Arduino firmware version string is kept separately as `Motors.FIRMWARE_VERSION` (a class-level constant, not the package version).
