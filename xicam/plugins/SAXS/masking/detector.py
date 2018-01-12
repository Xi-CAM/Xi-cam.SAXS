from xicam.plugins import ProcessingPlugin, Input, Output
from pyFAI.detectors import Detector
import numpy as np


class DetectorMaskPlugin(ProcessingPlugin):
    detector = Input(
        description='PyFAI detector instance; the geometry of the detector''s inactive area will be masked.',
        type=Detector)
    mask = Output(description='Mask array (1 is masked).',
                  type=np.ndarray)

    def evaluate(self):
        mask = self.detector.value.calc_mask()
        if mask is None: mask = np.zeros(self.detector.value.shape)
        self.mask.value = mask
