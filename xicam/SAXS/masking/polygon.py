from xicam.plugins import ProcessingPlugin, Input, Output
from pyFAI.detectors import Detector
import numpy as np


class PolygonMaskPlugin(ProcessingPlugin):
    detector = Input(
        description='PyFAI detector instance; the geometry of the detector''s inactive area will be masked.',
        type=Detector)
    polygon = Input(description='Polygon shape to mask (interior is masked)')
    mask = Output(description='Mask array (1 is masked).',
                  type=np.ndarray)

    def evaluate(self):
        raise NotImplementedError
