Quick start
===========

Launch the scanner application
-------------------------------

.. code-block:: bash

   python -m QPolargraph
   # or, after installation:
   qpolargraph

Pass ``-f`` / ``--fake`` to run with a simulated instrument (no hardware
required):

.. code-block:: bash

   qpolargraph --fake

The application opens a live plot showing the belt geometry and the scan
trajectory.  Use **Scan** to start a polar-arc sweep, or **Home** /
**Center** to move the payload to the home or centre position.

Embed in your own application
------------------------------

Subclass :class:`~QPolargraph.QScanner.QScanner` to add
experiment-specific data acquisition.  Override
:meth:`~QPolargraph.QScanner.QScanner._onDataReady` to merge in
additional measurement fields before emitting
:attr:`~QPolargraph.QScanner.QScanner.dataReady`:

.. code-block:: python

   from QPolargraph.QScanner import QScanner
   import numpy as np


   class MyScanner(QScanner):

       def _onDataReady(self, pos: np.ndarray) -> None:
           self.plotBelt(pos)
           self.dataReady.emit(
               {'x': float(pos[0]), 'y': float(pos[1])}
               | self.instrument.acquire())


   if __name__ == '__main__':
       MyScanner.example()

The :attr:`~QPolargraph.QScanner.QScanner.dataReady` signal emits a
``dict`` at each scan position.  A sequence of emitted dicts can be
collected directly into a :class:`pandas.DataFrame`:

.. code-block:: python

   rows = []
   scanner.dataReady.connect(rows.append)
   # after scan:
   import pandas as pd
   df = pd.DataFrame(rows)

Use a different scan pattern
----------------------------

Set the :attr:`~QPolargraph.QScanner.QScanner.SCAN_PATTERN` class
attribute to any :class:`~QPolargraph.patterns.QScanPattern.QScanPattern`
subclass:

.. code-block:: python

   from QPolargraph.QScanner import QScanner
   from QPolargraph.patterns.RasterScan import RasterScan


   class MyScanner(QScanner):
       SCAN_PATTERN = RasterScan


   if __name__ == '__main__':
       MyScanner.example()

Control the hardware directly
------------------------------

.. code-block:: python

   from qtpy.QtCore import QCoreApplication
   from QPolargraph.hardware.Polargraph import Polargraph
   import sys

   app = QCoreApplication(sys.argv)
   pg = Polargraph(ell=0.8, y0=0.15).find()   # auto-detects USB port
   print(pg.position)                           # (x, y, running) in metres
   pg.moveTo(0.0, 0.3)
   while pg.running():
       pass
   pg.release()
