from xicam.plugins import ProcessingPlugin, Input, Output, InOut
import numpy as np
import astroscrappy


class ZingerMaskPlugin(ProcessingPlugin):
    data = Input(description='Frame image data',
                 type=np.ndarray)
    mask = InOut(description='Mask array (1 is masked).',
                 type=np.ndarray)

    def evaluate(self):
        self.mask.value = np.logical_or(self.mask.value,
                                        astroscrappy.detect_cosmics(self.data.value, self.mask.value)[0])
