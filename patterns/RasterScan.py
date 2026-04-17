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
        x1, y1, x2, y2 = self.rect()
        x = np.arange(x1, x2, self.step * 1e-3)
        y = np.full_like(x, y1)
        y[1::2] = y2
        return np.vstack([x, y]).T

    def trajectory(self) -> np.ndarray:
        '''Return the raster path as a ``(2, npts)`` array for plotting.

        Returns
        -------
        numpy.ndarray
            ``(2, npts)`` array of ``(x, y)`` coordinates [m].
        '''
        return self.vertices().T
