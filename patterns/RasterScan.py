from QPolargraph.patterns.QScanPattern import QScanPattern
import numpy as np


class RasterScan(QScanPattern):

    '''Row-by-row raster scan pattern.

    Overrides :meth:`QScanPattern.vertices` to produce a zigzag path
    across the scan rectangle: odd columns scan top-to-bottom, even
    columns scan bottom-to-top.
    '''

    def vertices(self) -> np.ndarray:
        '''Return zigzag raster waypoints across the scan rectangle.

        Returns
        -------
        numpy.ndarray
            ``(nvertices, 2)`` array of ``(x, y)`` waypoints [m].
        '''
        x1, y1, x2, y2 = self.rect
        x = np.arange(x1, x2, self.step * 1e-3)
        y = np.full_like(x, y1)
        y[1::2] = y2
        return np.vstack([x, y]).T

    _TRAJECTORY_PTS = 20

    def trajectory(self) -> np.ndarray:
        '''Return the actual raster path as a ``(2, npts)`` array for plotting.

        Because the polargraph geometry is nonlinear, moving between two
        Cartesian waypoints traces a curve rather than a straight line.
        This method samples each segment at :attr:`_TRAJECTORY_PTS` points
        in step-index space and converts them back to Cartesian coordinates,
        giving an accurate picture of the true scan path.

        Falls back to the straight-line vertex path if no polargraph is
        attached.

        Returns
        -------
        numpy.ndarray
            ``(2, npts)`` array of ``(x, y)`` coordinates [m].
        '''
        pg = self.polargraph
        v = self.vertices()

        def i2r_vec(m, n):
            sm = pg.s0 + m * pg.ds
            sn = pg.s0 - n * pg.ds
            x = (sm ** 2 - sn ** 2) / (2. * pg.ell)
            ysq = (sn ** 2 + sm ** 2) / 2. - pg.ell ** 2 / 4. - x ** 2
            return x, np.sqrt(np.maximum(ysq, 0.))

        all_x, all_y = [], []
        for i in range(len(v) - 1):
            m0, n0 = pg.r2i(*v[i])
            m1, n1 = pg.r2i(*v[i + 1])
            endpoint = (i == len(v) - 2)
            t = np.linspace(0., 1., self._TRAJECTORY_PTS, endpoint=endpoint)
            x, y = i2r_vec(m0 + t * (m1 - m0), n0 + t * (n1 - n0))
            all_x.append(x)
            all_y.append(y)

        return np.vstack([np.concatenate(all_x), np.concatenate(all_y)])
