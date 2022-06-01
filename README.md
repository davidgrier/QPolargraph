# QPolargraph
PyQt5 implementation of a two-dimensional mechanical scanner.

A polargraph is a device that can translate a payload to an arbitrary
position within its scan area. The hardware implementation consists
of a toothed belt suspended between two stepping motors that
are positioned above and outside the scan area. Each stepping motor
has a toothed gear that engages with the teeth in the belt. 
The payload is attached to the belt and moves when the stepping motors
turn.

The stepping motors are controlled by an
[Arduino](https://www.arduino.cc/) 
microcontroller outfitted with an
[Adafruit Motor Shield](https://www.adafruit.com/product/1438)

This interface is intended for use in GUI applications created with
the PyQt5 widget framework. The Arduino should be connected to the
controlling computer through its USB interface.

## Software Setup
1. Use the Arduino application to read `acam3.ino`, which is located
   in the `arduino` subdirectory. Compile the sketch and upload it to 
   the Arduino.
   
2. `Polargraph.py` provides serial communication with the hardware.

3. `QPolargraphWidget.py` provides a GUI interface for controlling the hardware.

