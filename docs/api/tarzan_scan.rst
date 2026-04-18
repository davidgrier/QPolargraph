TarzanScan
==========

.. autoclass:: QPolargraph.patterns.TarzanScan.TarzanScan
   :members:
   :show-inheritance:

Mathematical background
-----------------------

A Tarzan scan cycle consists of four circular arcs, each driven by a
single motor.  Starting from a point :math:`p_0 = (x_0, y_\text{top})`
on the top edge, the cycle visits the right, bottom, left, and top
edges in turn before returning to :math:`p_4 = (x_1, y_\text{top})`.

The one-cycle advance map :math:`T : x_0 \mapsto x_1` has the
closed form

.. math::

   T(x_0) = -h + \sqrt{\!\left(\sqrt{(x_0 - h)^2 + B\,} - 2h\right)^2 + E\,}

where :math:`h = \ell/2` is half the motor separation and

.. math::

   B &= 4h\,x_\text{right} + y_\text{top}^2 - y_\text{bot}^2, \\
   E &= 4h\,x_\text{left}  + y_\text{bot}^2 - y_\text{top}^2
      = -B + 8h\,d_x.

Periodicity
~~~~~~~~~~~

The parameter :math:`B` governs whether the scan is periodic:

* :math:`B = 0` — :math:`T` is the identity map; every orbit is
  period-1 regardless of :math:`x_0`.  Adjust ``dy`` or ``height``
  until :math:`B \ne 0`.
* :math:`B \ne 0`, :math:`d_x = 0` — no fixed points exist; any
  :math:`x_0` yields an aperiodic scan.
* :math:`B \ne 0`, :math:`d_x \ne 0` — one fixed point
  :math:`x_0^* = h + d_x - B\,/\,(4\,d_x)`; avoid setting
  ``x0`` to this value.

Use :attr:`~TarzanScan.tarzan_B`, :attr:`~TarzanScan.is_degenerate`,
and :attr:`~TarzanScan.fixed_point` to inspect these conditions at
runtime.
