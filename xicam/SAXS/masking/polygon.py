from xicam.plugins import ProcessingPlugin, Input, Output, InOut
from pyFAI.detectors import Detector
import numpy as np
from pyqtgraph import ROI
from pyqtgraph.parametertree import parameterTypes
from typing import List, Tuple
from matplotlib.path import Path


class PolygonMask(ProcessingPlugin):
    name = 'Polygon Mask'

    ai = Input(
        description='PyFAI detector instance; the geometry of the detector''s inactive area will be masked.',
        type=Detector)
    polygon = Input(description='Polygon shape to mask (interior is masked)', type=List[Tuple[float, float]])
    mask = InOut(description='Mask array (1 is masked).', type=np.ndarray)

    def evaluate(self):
        if self.polygon.value is not None:
            # create path
            path = Path(np.vstack([self.polygon.value, self.polygon.value[-1]]),
                        [Path.MOVETO] + [Path.LINETO] * (len(self.polygon.value) - 1) + [Path.CLOSEPOLY])

            # create a grid
            ny, nx = self.ai.value.detector.shape
            x = np.linspace(0, nx, nx)
            y = np.linspace(0, ny, ny)
            xgrid, ygrid = np.meshgrid(x, y)
            pixel_coordinates = np.c_[xgrid.ravel(), ygrid.ravel()]

            # find points within path
            self.mask.value = np.logical_or(self.mask.value,
                                            np.flipud(path.contains_points(pixel_coordinates).reshape(ny, nx)))

    @property
    def parameter(self):
        if not (hasattr(self, '_param') and self._param):
            instructions = parameterTypes.TextParameter(name='Instructions',
                                                        value='Use the mouse to draw the mask. Click [Finish Mask] below when complete, or [Clear Selection] to start over.',
                                                        readonly=True)
            clearmask = parameterTypes.ActionParameter(name='Clear Selection')
            finishmask = parameterTypes.ActionParameter(name='Finish Mask')

            children = [instructions, clearmask, finishmask]
            self._param = parameterTypes.GroupParameter(name='Polygon Mask', children=children)
        return self._param
