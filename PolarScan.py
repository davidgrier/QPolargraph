from QPolargraph.QScanPattern import QScanPattern
import numpy as np


class PolarScan(QScanPattern):

    '''Arc-by-arc polar scan pattern centered on the left motor pulley.

    Overrides :meth:`QScanPattern.vertices` to sweep arcs of increasing
    radius across the scan rectangle.  Each arc is centered on the left
    motor pulley position at ``(-ell/2, 0)``.
    '''

    def _radii(self) -> np.ndarray:
        '''Return the arc radii [m] for the polar sweeps.

        Returns
        -------
        numpy.ndarray
            Radii at spacing ``step`` [mm] from the near to far corner
            of the scan rectangle.
        '''
        L = self.polargraph.ell / 2
        x1, y1, x2, y2 = self.rect()
        rmin = np.hypot(x1 + L, y1)
        rmax = np.hypot(x2 + L, y2)
        return np.arange(rmin, rmax, self.step * 1e-3)

    def _intercepts(self, r: float) -> list:
        '''Return the two points where arc of radius *r* crosses the scan rectangle.

        Parameters
        ----------
        r : float
            Arc radius measured from the left pulley [m].

        Returns
        -------
        list of [float, float]
            ``[start, end]`` intersection points ``[x, y]`` [m].
        '''
        p = -self.polargraph.ell / 2
        x1, y1, x2, y2 = self.rect()
        x1 -= p
        x2 -= p

        if r < np.hypot(x2, y1):
            r1 = [p + np.sqrt(r ** 2 - y1 ** 2), y1]
        else:
            r1 = [p + x2, np.sqrt(r ** 2 - x2 ** 2)]
        if r < np.hypot(x1, y2):
            r2 = [p + x1, np.sqrt(r ** 2 - x1 ** 2)]
        else:
            r2 = [p + np.sqrt(r ** 2 - y2 ** 2), y2]

        return [r1, r2]

    def vertices(self) -> np.ndarray:
        '''Return arc-endpoint waypoints for all polar sweeps.

        Returns
        -------
        numpy.ndarray
            ``(nvertices, 2)`` array of ``(x, y)`` waypoints [m].
        '''
        xy = np.array([])
        for n, r in enumerate(self._radii()):
            p1, p2 = self._intercepts(r)
            if (n % 2) == 0:
                p1, p2 = p2, p1
            xy = np.append(xy, [p1, p2])
        return xy.reshape(-1, 2)

    def trajectory(self) -> list:
        '''Return dense arc paths for all polar sweeps for display.

        Returns
        -------
        list of numpy.ndarray
            ``[x, y]`` coordinate arrays [m].
        '''
        L = self.polargraph.ell
        x = np.array([])
        y = np.array([])
        points = self.vertices().reshape(-1, 4)
        for n, r in enumerate(self._radii()):
            x1, y1, x2, y2 = points[n]
            s1 = np.sqrt(r ** 2 - 2. * L * x1)
            s2 = np.sqrt(r ** 2 - 2. * L * x2)
            s = np.linspace(s1, s2)
            thisx = (r ** 2 - s ** 2) / (2. * L)
            x = np.append(x, thisx)
            y = np.append(y, np.sqrt(r ** 2 - (L / 2. + thisx) ** 2))
        return [x, y]
