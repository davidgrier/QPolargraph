'''TarzanScan — geometry-native polargraph scan pattern.

Each move in a Tarzan scan involves exactly one motor.  The payload
swings on a circular arc (constant belt length on one side) while the
other motor is held fixed, tracing the natural coordinate lines of the
polargraph.  Because no interpolation is required, each arc is smooth
and free of the curvature artefacts seen in Cartesian raster scans.

One scan cycle visits the four sides of the scan rectangle in order:

1. **Top → right edge** : right belt fixed, left belt unwinds.
   Payload arcs around the right pulley.
2. **Right edge → bottom** : left belt fixed, right belt unwinds.
   Payload arcs around the left pulley.
3. **Bottom → left edge** : right belt fixed, left belt winds.
   Payload arcs around the right pulley.
4. **Left edge → top** : left belt fixed, right belt winds.
   Payload arcs around the left pulley.

After one cycle the payload returns to the top edge at a new
x-position x\\ :sub:`1`.  The sequence x\\ :sub:`0`, x\\ :sub:`1`,
x\\ :sub:`2`, … is determined entirely by the scan geometry and the
choice of x\\ :sub:`0`; cycles are repeated until the starting
x-position leaves the scan rectangle.
'''

from QPolargraph.patterns.QScanPattern import QScanPattern
import numpy as np
import logging

logger = logging.getLogger(__name__)


class TarzanScan(QScanPattern):

    '''Geometry-native scan pattern using alternating single-motor arcs.

    Overrides :meth:`~QPolargraph.QScanPattern.QScanPattern.vertices`
    and :meth:`~QPolargraph.QScanPattern.QScanPattern.trajectory` to
    produce a sequence of circular arcs, each driven by a single motor.
    Scan data are collected on all four arc segments of every cycle.

    Parameters
    ----------
    x0 : float, optional
        Starting x-coordinate on the top edge of the scan area [m].
        Default: ``0.0``.  Adjust until the trajectory covers the
        scan area satisfactorily.

    Notes
    -----
    All parameters inherited from
    :class:`~QPolargraph.QScanPattern.QScanPattern`
    (``width``, ``height``, ``dx``, ``dy``, ``step``) are also accepted.
    '''

    _TRAJECTORY_PTS = 50

    def __init__(self, *args, x0: float = 0., **kwargs):
        super().__init__(*args, **kwargs)
        self._x0 = float(x0)

    @property
    def x0(self) -> float:
        '''Starting x-coordinate on the top edge of the scan area [m].'''
        return self._x0

    @x0.setter
    def x0(self, value: float) -> None:
        self._x0 = float(value)

    @property
    def tarzan_B(self) -> float:
        '''Key parameter of the Tarzan map [m²].

        Defined as ``B = 4h·x_right + y_top² − y_bottom²`` where
        ``h = ell/2``.  The Tarzan map ``T(x₀)`` has a closed form
        involving only ``B`` and its partner
        ``E = −B + 8h·dx``.

        When ``B = 0`` the map is the identity and every orbit is
        period-1 regardless of ``x0``; adjust ``dy`` or ``height``
        until ``B ≠ 0``.
        '''
        if self.polargraph is None:
            return 0.
        x_left, y_top, x_right, y_bottom = self.rect()
        h = self.polargraph.ell / 2.
        return 4. * h * x_right + y_top**2 - y_bottom**2

    @property
    def is_degenerate(self) -> bool:
        '''``True`` when the scan geometry produces a periodic Tarzan map.

        Degeneracy (``B ≈ 0``) means every orbit is period-1: the scan
        repeats the same path on every cycle regardless of ``x0``.
        Increase or decrease ``dy`` (or change ``height``) to break the
        degeneracy.
        '''
        if self.polargraph is None:
            return False
        scale = self.polargraph.ell * self.width
        return abs(self.tarzan_B) < 1e-9 * scale

    @property
    def fixed_point(self) -> float | None:
        '''Unique fixed point of the Tarzan map [m], or ``None``.

        Returns ``x0* = h + dx − B / (4·dx)`` when ``B ≠ 0`` and
        ``dx ≠ 0``.  Passing ``x0 = fixed_point`` produces a
        period-1 orbit (identical repeated scans); avoid it.

        Returns ``None`` in two cases:

        * ``dx = 0`` and ``B ≠ 0``: no fixed points exist — any
          ``x0`` yields an aperiodic scan.
        * ``B = 0``: all ``x0`` are fixed points (degenerate geometry).
        '''
        if self.polargraph is None or self.is_degenerate:
            return None
        if abs(self.dx) < 1e-12:
            return None
        h = self.polargraph.ell / 2.
        return h + self.dx - self.tarzan_B / (4. * self.dx)

    # ------------------------------------------------------------------
    # Internal geometry helpers
    # ------------------------------------------------------------------

    def _pulley_positions(self) -> tuple[np.ndarray, np.ndarray]:
        '''Return the (x, y) positions of the left and right pulleys [m].'''
        h = self.polargraph.ell / 2.
        return np.array([-h, 0.]), np.array([h, 0.])

    def _cycle(self, p_start: np.ndarray) -> list[np.ndarray] | None:
        '''Compute the four arc-corner points for one Tarzan cycle.

        Parameters
        ----------
        p_start : np.ndarray
            Starting point ``(x, y)`` on the top edge of the scan area [m].

        Returns
        -------
        list of np.ndarray or None
            ``[P1, P2, P3, P4]`` — arc endpoints at the right edge,
            bottom edge, left edge, and top edge respectively [m].
            Returns ``None`` if any arc fails to reach its target boundary
            (scan geometry is incompatible with a full cycle from this point).
        '''
        x_left, y_top, x_right, y_bottom = self.rect()
        L, R = self._pulley_positions()

        # Segment 1: arc around R (right pulley), top edge → right edge
        s2 = np.linalg.norm(p_start - R)
        d1 = s2**2 - (x_right - R[0])**2
        if d1 < 0:
            return None
        p1 = np.array([x_right, np.sqrt(d1)])

        # Segment 2: arc around L (left pulley), right edge → bottom edge
        s1 = np.linalg.norm(p1 - L)
        d2 = s1**2 - y_bottom**2
        if d2 < 0:
            return None
        p2 = np.array([L[0] + np.sqrt(d2), y_bottom])

        # Segment 3: arc around R (right pulley), bottom edge → left edge
        s2 = np.linalg.norm(p2 - R)
        d3 = s2**2 - (x_left - R[0])**2
        if d3 < 0:
            return None
        p3 = np.array([x_left, np.sqrt(d3)])

        # Segment 4: arc around L (left pulley), left edge → top edge
        s1 = np.linalg.norm(p3 - L)
        d4 = s1**2 - y_top**2
        if d4 < 0:
            return None
        p4 = np.array([L[0] + np.sqrt(d4), y_top])

        return [p1, p2, p3, p4]

    def _arc_points(self, p_start: np.ndarray, p_end: np.ndarray,
                    center: np.ndarray) -> np.ndarray:
        '''Sample :attr:`_TRAJECTORY_PTS` points along a circular arc.

        Parameters
        ----------
        p_start : np.ndarray
            Arc start point ``(x, y)`` [m].
        p_end : np.ndarray
            Arc end point ``(x, y)`` [m].
        center : np.ndarray
            Arc center ``(x, y)`` [m] (pulley position).

        Returns
        -------
        numpy.ndarray
            ``(n, 2)`` array of ``(x, y)`` points along the arc [m].
        '''
        r = np.linalg.norm(p_start - center)
        theta_start = np.arctan2(p_start[1] - center[1],
                                 p_start[0] - center[0])
        theta_end = np.arctan2(p_end[1] - center[1],
                               p_end[0] - center[0])
        theta = np.linspace(theta_start, theta_end, self._TRAJECTORY_PTS)
        x = center[0] + r * np.cos(theta)
        y = center[1] + r * np.sin(theta)
        return np.column_stack([x, y])

    # ------------------------------------------------------------------
    # QScanPattern interface
    # ------------------------------------------------------------------

    def vertices(self) -> np.ndarray:
        '''Return arc-corner waypoints for all Tarzan scan cycles.

        Iterates cycles starting from ``(x0, y_top)`` until the
        next starting x-position leaves ``[x_left, x_right]``.

        Falls back to the base-class perimeter rectangle when no
        polargraph is attached.

        Returns
        -------
        numpy.ndarray
            ``(nvertices, 2)`` array of ``(x, y)`` waypoints [m].
        '''
        if self.polargraph is None:
            return super().vertices()

        if self.is_degenerate:
            logger.warning(
                'TarzanScan: degenerate geometry (B ≈ 0) — every cycle '
                'repeats the same path. Adjust dy or height until '
                'ell·width ≠ height·(y_top + y_bottom).')

        x_left, y_top, x_right, _ = self.rect()
        p = np.array([self._x0, y_top])
        pts = [p.copy()]

        while x_left <= p[0] <= x_right:
            result = self._cycle(p)
            if result is None:
                break
            p1, p2, p3, p4 = result
            pts.extend([p1, p2, p3, p4])
            if p4[0] <= p[0]:
                # Fixed point or backward scan: record the cycle and stop.
                break
            p = p4

        return np.array(pts)

    def trajectory(self) -> np.ndarray:
        '''Return the Tarzan scan path sampled along each arc.

        Each segment between consecutive vertices is a true circular arc;
        this method samples each arc at :attr:`_TRAJECTORY_PTS` points
        for accurate display.

        Falls back to the straight-line vertex path when no polargraph
        is attached.

        Returns
        -------
        numpy.ndarray
            ``(2, npts)`` array of ``(x, y)`` coordinates [m].
        '''
        if self.polargraph is None:
            return super().trajectory()

        L, R = self._pulley_positions()
        # Segments within each cycle alternate: R, L, R, L
        centers = [R, L, R, L]

        v = self.vertices()
        if len(v) < 2:
            return super().trajectory()

        arcs = []
        for i in range(len(v) - 1):
            center = centers[i % 4]
            arc = self._arc_points(v[i], v[i + 1], center)
            arcs.append(arc)

        pts = np.vstack(arcs)
        return pts.T
