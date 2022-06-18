from QPolargraph.QScanPattern import QScanPattern
import numpy as np


class PolarScan(QScanPattern):

    def _radii(self):
        '''Returns the radii [m] of the polar sweeps in the scan pattern'''
        L = self.polargraph.ell/2
        x1, y1, x2, y2 = self.rect()
        rmin = np.hypot(x1 + L, y1)
        rmax = np.hypot(x2 + L, y2)
        return np.arange(rmin, rmax, self.step*1e-3)  # step is measured in mm

    def _intercepts(self, r):
        '''Returns points where polar sweep intersects bounding rectangle'''
        p = -self.polargraph.ell/2
        x1, y1, x2, y2 = self.rect()
        x1 -= p
        x2 -= p

        if (r < np.hypot(x2, y1)):
            r1 = [p + np.sqrt(r**2 - y1**2), y1]
        else:
            r1 = [p + x2, np.sqrt(r**2 - x2**2)]
        if (r < np.hypot(x1, y2)):
            r2 = [p + x1, np.sqrt(r**2 - x1**2)]
        else:
            r2 = [p + np.sqrt(r**2 - y2**2), y2]

        return [r1, r2]

    def vertices(self):
        '''overrides QScanPattern.vertices()'''
        xy = np.array([])
        for n, r in enumerate(self._radii()):
            p1, p2 = self._intercepts(r)
            if (n % 2) == 0:
                p1, p2 = p2, p1
            xy = np.append(xy, [p1, p2])
        return xy.reshape(-1, 2)

    def trajectory(self):
        '''overrides QScanPattern.trajectory()'''
        L = self.polargraph.ell
        x = np.array([])
        y = np.array([])
        points = self.vertices().reshape(-1, 4)
        for n, r in enumerate(self._radii()):
            x1, y1, x2, y2 = points[n]
            s1 = np.sqrt(r**2 - 2.*L*x1)
            s2 = np.sqrt(r**2 - 2.*L*x2)
            s = np.linspace(s1, s2)
            thisx = (r**2 - s**2)/(2.*L)
            x = np.append(x, thisx)
            y = np.append(y, np.sqrt(r**2 - (L/2. + thisx)**2))
        return [x, y]
