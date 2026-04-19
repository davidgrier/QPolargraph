Changelog
=========

1.3.1 (2026-04-19)
------------------

- ``QScanPattern``: removed ``QCoreApplication.processEvents()`` from the
  scan loop now that ``QSerialInterface.receive()`` no longer blocks the
  event loop (requires ``QInstrument>=2.4``).
- ``QScanner._startMove``: removed outdated docstring note about
  ``processEvents()``.
- ``pyproject.toml``: bumped ``QInstrument`` dependency to ``>=2.4``.

1.3.0 (2026-04-19)
------------------

- ``acam3`` firmware 3.5.0: raised baud rate from 9600 to 115200; removed
  diagnostic ``I`` command; ``P`` query now always responds ``P:n1:n2:running``
  (running state encoded as a third field rather than an ambiguous prefix);
  ``n1``/``n2`` made local to the functions that use them.
- ``Motors.comm``: updated baud rate to ``Baud115200``.
- ``Motors.indexes``: updated parser for the new ``P:n1:n2:running`` response format.

1.2.4 (2026-04-18)
------------------

- ``QScanner.plotData``: fixed ``pg.hsvColor`` keyword argument from
  ``s=`` to ``sat=`` (correct pyqtgraph API).

1.2.3 (2026-04-18)
------------------

- ``QScanner.plotData``: renamed ``value`` parameter to ``saturation``
  and mapped it to HSV saturation (``s=``) instead of brightness.
  Loud/strong areas render as pure hue; quiet/weak areas appear white.

1.2.2 (2026-04-18)
------------------

- ``QScanner.plotData``: added optional ``value`` parameter (HSV brightness,
  default ``1.0``) so subclasses can encode a second scalar quantity as
  point brightness without changing existing behavior.

1.2.1 (2026-04-18)
------------------

- ``QScanPattern.rect``: converted from a plain method to a ``@property``
  so that callers can write ``pattern.rect`` consistently with other
  geometric properties (``width``, ``height``, ``step``, etc.).
  Updated all internal callers in ``PolarScan``, ``RasterScan``, and
  ``TarzanScan``.

1.2.0 (2026-04-18)
------------------

- ``QScanPattern``: replaced ``_moving`` / ``_scanning`` bool flags with a
  ``ScanState`` enum (``IDLE``, ``MOVING``, ``SCANNING``).  Added
  ``moving()`` predicate and updated ``scanning()`` to use the enum.
- ``QScanPattern``: added ``closeRequested`` signal, emitted (via
  ``_setIdle()``) when the state returns to IDLE after
  ``interruptAndClose()`` was called.
- ``QScanPattern.home`` / ``center``: set state to MOVING before the move
  and call ``_setIdle()`` on completion.
- ``QScanPattern.scan``: full state-machine transitions
  IDLE→MOVING→SCANNING→MOVING→IDLE; skips home only on close-interrupt.
- ``QScanner.closeEvent``: use ``moving()`` (not ``scanning()``) and
  ``interruptAndClose()``; drop the 100 ms timer — ``closeRequested``
  triggers ``close()`` via a ``QueuedConnection`` when motion stops.
- ``QScanner.toggleScan``: use ``moving()`` so Stop works during the
  initial positioning move, not only during active data collection.

1.1.7 (2026-04-18)
------------------

- ``QScanPattern``: added ``interruptAndClose()`` method that sets a new
  ``_closing`` flag in addition to ``_interrupt``.  ``scan()`` now skips
  ``home()`` only when ``_closing`` is set (window-close path), preserving
  the original behavior of returning home after a normal Stop.
- ``QScanner.closeEvent``: call ``interruptAndClose()`` instead of
  ``interrupt()`` so Stop still goes home but window-close does not hang.

1.1.6 (2026-04-18)
------------------

- ``QScanPattern.scan``: set ``_scanning = True`` before the initial move to
  the start position so that ``closeEvent`` interrupts rather than accepts
  a close request during early scan setup, preventing a hang in ``time.sleep``.

1.1.5 (2026-04-18)
------------------

- ``QScanPattern.scan``: skip ``home()`` when the scan was interrupted,
  preventing a hang when the application is closed during an active scan.

1.1.4 (2026-04-18)
------------------

- ``FakePolargraph.moveTo``: number of trajectory waypoints is now
  proportional to arc length (``dist_mm / speed / step_delay``),
  matching the real hardware which records data at equal time intervals.
  Longer arcs produce more data points than shorter ones.  Falls back
  to one-step-per-motor-step when ``step_delay=0`` (automated tests).

1.1.3 (2026-04-18)
------------------

- ``FakePolargraph.moveTo``: interpolates in motor step-index space
  rather than Cartesian space, then converts via ``i2r``.  The simulated
  trajectory now follows arcs matching the real belt-drive geometry
  instead of straight lines.

1.1.2 (2026-04-18)
------------------

- Fixed ``__init__.py`` lazy ``__getattr__``: resolved value is now cached
  into ``globals()`` so that Python's submodule binding side effect cannot
  shadow the class with the module object on subsequent accesses.

1.1.1 (2026-04-17)
------------------

- Refactored ``FlashFirmware``: imports ``FIRMWARE_VERSION`` from
  ``Motors`` instead of duplicating ``_firmware_version()``.
- Fixed ``PolarScan.trajectory()``: now returns ``np.ndarray`` with
  shape ``(2, n)`` consistent with all other scan patterns.
- Refactored ``QScanPatternWidget``: extracted ``_FIELDS`` class
  constant; added type hints.
- Refactored ``QScanPattern``: ``polargraph`` parameter now annotated
  ``Polargraph | None`` via ``TYPE_CHECKING`` guard.

1.1.0 (2026-04-17)
------------------

- Added ``TarzanScan``: geometry-native scan pattern where each move engages
  exactly one motor; the payload swings on a circular arc along the natural
  coordinate lines of the polargraph.
- Added ``TarzanScan.tarzan_B``, ``is_degenerate``, and ``fixed_point``
  properties that characterise the periodicity of the scan map.
- Added ``-r`` / ``--raster``, ``-p`` / ``--polar``, and ``-t`` / ``--tarzan``
  command-line flags to ``qpolargraph`` for selecting the scan pattern at
  launch (default: polar).
- Redesigned ``PolargraphWidget``: removed nested ``Configuration`` and
  ``Belt Drive`` group boxes; all controls now in a compact flat grid with
  right-aligned labels beside spinboxes.
- Redesigned ``RasterScanWidget``: replaced label-above-spinbox layout with
  the same label-beside-spinbox grid used by ``PolargraphWidget``.
- Improved startup layout: plot panel maximised by default; scan setup panel
  takes all spare vertical space in the controls column.

1.0.2 (2026-04-17)
------------------

- Fixed ``QScanner``: serial I/O stays on the main thread; ``processEvents()``
  in the scan loop keeps the UI responsive without crossing thread boundaries.
- Added ``Motors.scan_i2c()`` diagnostic to report I2C devices found on the
  Arduino's bus — useful for diagnosing motor shield detection failures.
- Added ``Motors.scan_i2c()`` error hints when motor shield is not detected.
- Firmware 3.3.2: explicit ``Wire.begin()``; retry ``AFMS.begin()`` up to
  5 times on startup; ``I`` command scans and reports I2C bus addresses.

1.0.1 (2026-04-17)
------------------

- Fixed ``FlashFirmware``: use ``systemLocation()`` instead of ``portName()``
  so ``avrdude`` receives the full device path (e.g. ``/dev/tty.usbmodem2101``).
- Fixed ``FlashFirmware``: use ``arduino-cli lib upgrade`` to update already-installed
  Arduino libraries before flashing.

1.0.0 (2026-04-15)
------------------

- Initial release as a polished, cross-platform package.
- Migrated from PyQt5 to qtpy for Qt-binding independence.
- Replaced MIT license with GPL v3 for consistency with QInstrument.
- Added ``pyproject.toml``, GitHub Actions CI/CD, and git hooks.
- Added ``__main__.py`` entry point and ``qpolargraph`` GUI script.
