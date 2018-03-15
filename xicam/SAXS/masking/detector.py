from xicam.plugins import ProcessingPlugin, Input, Output, InOut
from pyFAI import AzimuthalIntegrator
import numpy as np


class DetectorMaskPlugin(ProcessingPlugin):
    name = 'Detector Mask'
    ai = Input(
        description='PyFAI azimuthal integrator instance; the geometry of the detector''s inactive area will be masked.',
        type=AzimuthalIntegrator)
    mask = InOut(description='Mask array (1 is masked).',
                  type=np.ndarray)

    def evaluate(self):
        if self.ai.value and self.ai.value.detector:
            mask = self.ai.value.detector.calc_mask()
            if mask is None: mask = np.zeros(self.ai.value.detector.shape)
            self.mask.value = np.logical_or(self.mask.value, mask)
