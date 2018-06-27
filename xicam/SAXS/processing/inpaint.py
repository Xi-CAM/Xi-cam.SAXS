from xicam.plugins import ProcessingPlugin, Input, Output, InOut
import numpy as np
from pyFAI.ext.reconstruct import reconstruct


class InPaint(ProcessingPlugin):
    name = 'Inpaint (pyFAI)'

    data = InOut(description='2d array representing intensity for each pixel',
                 type=np.ndarray)
    mask = Input(description='Array (same size as image) with 1 for masked pixels, and 0 for valid pixels',
                 type=np.ndarray)
    inpaint = Output(description='2d array with masking pixels ''reconstructed''', type=np.ndarray)

    def evaluate(self):
        self.inpaint.value = reconstruct(self.data.value, self.mask.value)
