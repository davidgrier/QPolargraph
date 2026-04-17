Changelog
=========

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
