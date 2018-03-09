from xicam.plugins import ProcessingPlugin, Input, Output
from pyFAI.detectors import Detector
import numpy as np
from pyqtgraph import ROI
from pyqtgraph.parametertree import parameterTypes


class PolygonMaskPlugin(ProcessingPlugin):
    name = 'Polygon Mask'

    detector = Input(
        description='PyFAI detector instance; the geometry of the detector''s inactive area will be masked.',
        type=Detector)
    polygon = Input(description='Polygon shape to mask (interior is masked)', type=ROI)
    mask = Output(description='Mask array (1 is masked).',
                  type=np.ndarray)

    def evaluate(self):
        self.mask.value = self.polygon.value  # ...

    @property
    def parameter(self):
        children = [parameterTypes.ActionParameter(name='Draw Mask')]
        return parameterTypes.GroupParameter(name='Polygon Mask', children=children)
