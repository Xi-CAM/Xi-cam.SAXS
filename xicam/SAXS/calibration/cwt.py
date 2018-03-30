import numpy as np
from camsaxs import cwt2d
from xicam.plugins import ProcessingPlugin, Input, Output


class RickerWave(ProcessingPlugin):

    # inputs
    data = Input(description='Calibrant frame image data',
                 type=np.ndarray)
    mask = Input(description='Array with 1 for masked pixels, and 0 for valid pixels',
                 type=np.ndarray)
    domain = Input(
        description='Search domain in pixels: [r_min, r_max]', type=list)
    scale = Input(description='Approxmate intensity along the ring',
                  type=float, default=1)
    width = Input(
        description='Approximate width of the AgB ring in pixels', type=float, default=5)

    # output
    center = Output(
        description='Approximated position of the direct beam center', type=np.ndarray)

    def evaluate(self):
        self.center.value,_ = cwt2d(self.data.value, domain=self.domain.value,
                                  scale=self.scale.value,
                                  width=self.width.value)
