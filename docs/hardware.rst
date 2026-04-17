Hardware
========

Components
----------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Component
     - Description
   * - 2× Nema-17 stepper motor
     - Mounted above and to either side of the scan area
   * - GT2 timing belt
     - Spans both motors; payload hangs from its midpoint
   * - GT2 drive gear (25-tooth)
     - One per motor; engages the belt
   * - `Adafruit Motor Shield v2 <https://www.adafruit.com/product/1438>`_
     - Drives both steppers from a single Arduino
   * - Arduino (Uno or compatible)
     - Runs the ``acam3`` firmware; connects to the host via USB

The belt forms a V-shape between the two motors.  Each motor changes the
length of one side of the V, moving the payload in two dimensions.

Firmware
--------

The Arduino must be flashed with ``hardware/arduino/acam3/acam3.ino``
before first use.  The easiest way is the built-in installer:

.. code-block:: bash

   qpolargraph-flash

This opens a dialog that detects the attached Arduino, installs any
missing Arduino libraries (``Adafruit Motor Shield V2 Library``,
``AccelStepper``), compiles, and uploads the firmware — all without
opening the Arduino IDE.  It requires
`arduino-cli <https://arduino.github.io/arduino-cli/>`_ to be installed
and on ``PATH``.

Alternatively, open ``hardware/arduino/acam3/acam3.ino`` in the
`Arduino IDE <https://www.arduino.cc/en/software>`_ and upload manually.

The firmware and package versions are coupled: :meth:`Motors.identify`
checks that the connected Arduino reports the expected firmware version
and that the Adafruit Motor Shield is detected at I2C address ``0x60``,
refusing to open the port if either check fails.

You can also integrate the flash dialog into a ``QMainWindow`` application
as a menu action (see :class:`~QPolargraph.FlashFirmware.FlashDialog`).

Calibration
-----------

Five geometric parameters describe the polargraph.  Set them in the
:class:`~QPolargraph.hardware.QPolargraphWidget.QPolargraphWidget` control
panel or pass them directly to
:class:`~QPolargraph.hardware.Polargraph.Polargraph`:

.. list-table::
   :header-rows: 1
   :widths: 20 15 65

   * - Parameter
     - Default
     - Description
   * - ``ell``
     - 1.0 m
     - Horizontal distance between the two motor pulley centres
   * - ``y0``
     - 0.1 m
     - Vertical distance from the pulleys to the home position
   * - ``pitch``
     - 2.0 mm
     - GT2 belt tooth pitch
   * - ``circumference``
     - 25
     - Number of belt teeth on the drive gear
   * - ``steps``
     - 200
     - Motor steps per revolution

Measure ``ell`` and ``y0`` with a ruler after mounting the motors.
``pitch``, ``circumference``, and ``steps`` are determined by the belt
and gear specifications and normally do not need to change.

Settings are saved to ``~/.QScanner/`` automatically when the application
closes, so calibration only needs to be done once.
