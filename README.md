# QPolargraph
PyQt5 implementation of a two-dimensional mechanical scanner.

A [polargraph](http://www.polargraph.co.uk/) 
is a device that can translate a payload to an arbitrary
position within its scan area. Originally developed by Sandy Noble as
an automated drawing machine, this class of scanners is easy to set up,
scales naturally to large scan areas, offers millimeter-scale precision and accuracy, 
and is very cost-effective. The version used in this project consists
of a GT2 toothed belt suspended between two Nema-17 stepping motors that
are positioned above and outside the scan area. Each stepping motor
has a toothed gear that engages with the belt.
The payload is attached to the middle of the belt and hangs down from
the motors, forming the belt into a V shape. The motors move the payload
by changing the lengths of the two sides of the V.

The stepping motors are controlled by an
[Arduino](https://www.arduino.cc/) 
microcontroller outfitted with an
[Adafruit Motor Shield](https://www.adafruit.com/product/1438).

This interface is intended for use in GUI applications created with
the PyQt5 widget framework. The Arduino should be connected to the
controlling computer through its USB interface.

## Software Setup
1. Use the Arduino application to read `acam3.ino`, which is located
   in the `arduino/acam3/` subdirectory.
   Compile the sketch and upload it to the Arduino.
   
2. `Polargraph.py` provides serial communication with the hardware.

3. `QPolargraphWidget.py` provides a GUI interface for controlling the hardware.

## Dependencies
1. [QInstrument](https://github.com/davidgrier/QInstrument)
2. [PyQt5](https://pypi.org/project/PyQt5/)
3. [pyqtgraph](https://www.pyqtgraph.org/)
4. [Arduino](https://www.arduino.cc/)

## Acknowledgements

Work on this project at New York University is supported by
the National Science Foundation of the United States under award
number DMR-2104837
