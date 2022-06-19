# QPolargraph
PyQt5 implementation of a two-dimensional mechanical scanner.

A [polargraph](http://www.polargraph.co.uk/) 
is a device that can translate a payload to an arbitrary
position within its scan area.
[Originally developed](http://juerglehni.com/works/hektor) by
Jürg Lehni and Uli Franke as an automated drawing machine, this class of scanners is easy to set up,
scales naturally to large scan areas, offers millimeter-scale precision and accuracy, 
and is very cost-effective.

The hardware implementation in this project consists
of a GT2 timing belt suspended between two Nema-17 stepping motors that
are positioned above and outside the scan area. Each stepping motor
has a toothed gear that engages with the belt.
The payload is attached to the middle of the belt and hangs down from
the motors, forming the belt into a V shape. The motors move the payload
by changing the lengths of the two sides of the V.
The stepping motors are controlled by an
[Arduino](https://www.arduino.cc/) 
microcontroller outfitted with an
[Adafruit Motor Shield](https://www.adafruit.com/product/1438).
The Arduino is connected to the controlling computer through its USB interface.

The software interface provided in this repository is intended
for use in GUI applications created with
the PyQt5 widget framework. 

## Software Setup
1. Use the Arduino application to load [`acam3.ino`](/arduino/acam3/acam.ino) onto the Arduino.
2. [`Polargraph.py`](/Polargraph.py) provides serial communication with the hardware.
3. [`QPolargraphWidget.py`](/QPolargraphWidget.py) provides a GUI interface for controlling the hardware.
4. [`QScanner.py`](/QScanner.py) is an application framework that controls the scanner and
provides real-time graphical feedback of a scan. It is intended to be subclassed for
larger-scale applications.

## Dependencies
1. [QInstrument](https://github.com/davidgrier/QInstrument)
2. [PyQt5](https://pypi.org/project/PyQt5/)
3. [pyqtgraph](https://www.pyqtgraph.org/)
4. [Arduino](https://www.arduino.cc/)

## Acknowledgements

Work on this project at New York University is supported by
the National Science Foundation of the United States under award
number DMR-2104837
