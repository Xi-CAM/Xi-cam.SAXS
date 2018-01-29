from xicam.plugins import ProcessingPlugin, Input, Output
import numpy as np


class HorizontalCutPlugin(ProcessingPlugin):
    data = Input(description='Frame image data', type=np.ndarray)
    qx = Input(description='qx coordinate corresponding to data', type=np.ndarray)
    mask = Input(description='Frame image data', type=np.ndarray, default=None)

    # Make qx range a single parameter, type = tuple
    qxminimum = Input(description='qx minimum limit', type=int)
    qxmaximum = Input(description='qx maximum limit', type=int)

    horizontalcut = Output(description='mask (1 is masked) with dimension of data', type=np.ndarray)

    def evaluate(self):
        if self.mask.value is not None:
            self.horizontalcut.value = np.logical_or(self.mask.value, self.qx < self.qxminimum.value,
                                                     self.qx > self.qxmaximum.value)
        else:
            self.horizontalcut.value = np.logical_or(self.qx < self.qxminimum.value, self.qx > self.qxmaximum.value)
