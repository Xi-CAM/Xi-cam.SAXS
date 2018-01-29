from xicam.plugins import ProcessingPlugin, Input, Output
import numpy as np


class VerticalCutPlugin(ProcessingPlugin):
    data = Input(description='Frame image data', type=np.ndarray)
    qz = Input(description='qz coordinate corresponding to data', type=np.ndarray)

    mask = Input(description='Frame image data', type=np.ndarray, default=None)

    # Make qz range a single parameter, type = tuple
    qzminimum = Input(description='qz minimum limit', type=int)
    qzmaximum = Input(description='qz maximum limit', type=int)

    verticalcut = Output(description='mask (1 is masked) with dimension of data', type=np.ndarray)

    def evaluate(self):
        if self.mask.value is not None:
            self.verticalcut.value = np.logical_or(self.mask.value, self.qz < self.qzminimum.value,
                                                   self.qz > self.qzmaximum.value)
        else:
            self.verticalcut.value = np.logical_or(self.qz.value < self.qzminimum.value,
                                                   self.qz.value > self.qzmaximum.value)
