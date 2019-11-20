from xicam.plugins import ProcessingPlugin, Input, Output, InOut
from pyFAI.azimuthalIntegrator import AzimuthalIntegrator
import fabio
import numpy as np


class FileMask(ProcessingPlugin):
    name = 'File Mask'

    mask = InOut(description='Mask array (1 is masked).',
                 type=np.ndarray)
    ai = Input(
        description='PyFAI azimuthal integrator instance; the geometry of the detector''s inactive area will be masked.',
        type=AzimuthalIntegrator)
    path = Input(description='File path to image mask file.', type=str, default='')

    def evaluate(self):
        if not self.path.value:
            return

        mask = fabio.open(self.path.value).data.astype(np.bool_)

        if not mask.shape == self.ai.value.detector.shape:
            raise IndexError('Mask file does not match detector shape.')

        if self.mask.value is None: self.mask.value = np.zeros(self.ai.value.detector.shape).astype(np.bool_)
        self.mask.value = np.logical_or(self.mask.value, mask)
