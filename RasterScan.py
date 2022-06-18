from QPolargraph.QScanPattern import QScanPattern
import numpy as np


class RasterScan(QScanPattern):

    def vertices(self):
        '''overrides QScanPattern.vertices()'''

        x1, y1, x2, y2 = self.rect()
        x = np.arange(x1, x2, self.step*1e-3)
        y = np.full_like(x, y1)
        y[1::2] = y2
        return np.vstack([x, y]).T

    def trajectory(self):
        '''overrides QScanPattern.trajectory()'''

        return self.vertices().T
