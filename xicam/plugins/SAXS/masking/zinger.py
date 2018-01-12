from xicam.plugins import ProcessingPlugin, Input, Output
import numpy as np


class ZingerMaskPlugin(ProcessingPlugin):
    data = Input(description='Frame image data',
                 type=np.ndarray)
    mask = Output(description='Mask array (1 is masked).',
                  type=np.ndarray)

    def evaluate(self):
        raise NotImplementedError
