from xicam.plugins import ProcessingPlugin, Input, Output
import numpy as np
from xicam.plugins.hint import VerticalROI

class VerticalCutPlugin(ProcessingPlugin):
    data = Input(description='Frame image data', type=np.ndarray)
    qz = Input(description='qz coordinate corresponding to data', type=np.ndarray)

    mask = Input(description='Frame image data', type=np.ndarray, default=None)

    # Make qz range a single parameter, type = tuple
    qzminimum = Input(description='qz minimum limit', type=int)
    qzmaximum = Input(description='qz maximum limit', type=int)

    cut = Output(description='mask (1 is masked) with dimension of data', type=np.ndarray)

    hints = [VerticalROI(qzminimum, qzmaximum)]

    def evaluate(self):
        if self.mask.value is not None:
            self.cut.value = np.logical_or(self.mask.value, self.qz < self.qzminimum.value,
                                           self.qz > self.qzmaximum.value)
        else:
            self.cut.value = np.logical_or(self.qz.value < self.qzminimum.value,
                                           self.qz.value > self.qzmaximum.value)
