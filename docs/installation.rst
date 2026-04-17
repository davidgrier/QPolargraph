Installation
============

Requirements
------------

- Python 3.10 or later
- A Qt binding: PyQt5, PyQt6, PySide2, or PySide6
- ``qtpy >= 2.0``
- ``numpy >= 1.20``
- ``pyqtgraph >= 0.13``
- ``parse >= 1.19``
- `QInstrument <https://github.com/davidgrier/QInstrument>`_ >= 2.2

Install from PyPI
-----------------

.. code-block:: bash

   pip install QPolargraph

A Qt binding is not installed automatically.  Install one separately:

.. code-block:: bash

   pip install PyQt6

Install from source
-------------------

.. code-block:: bash

   git clone https://github.com/davidgrier/QPolargraph
   cd QPolargraph
   python -m venv .qp
   source .qp/bin/activate          # Windows: .qp\Scripts\activate
   pip install -e ".[dev]"
   pip install PyQt6

Firmware
--------

Before first use, the Arduino must be flashed with the ``acam3`` firmware
bundled in ``hardware/arduino/acam3/``.  See :doc:`hardware` for full
instructions.
