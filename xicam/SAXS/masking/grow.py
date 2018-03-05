from xicam.plugins import ProcessingPlugin, Input, InOut
from scipy.ndimage import morphology
import numpy as np


class GrowMask(ProcessingPlugin):
    mask = InOut(description='Mask array (1 is masked).',
                 type=np.ndarray)
    size = Input(description='Distance to grow the mask (px); used as kernel size')

    def evaluate(self):
        y, x = np.ogrid[-self.size.value:self.size.value + 1,
               -self.size.value:self.size.value + 1]
        kernel = x ** 2 + y ** 2 <= self.size.value ** 2
        morphology.binary_dilation(self.mask.value, kernel, output=self.mask.value)  # write-back to mask
