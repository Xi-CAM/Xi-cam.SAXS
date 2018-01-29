import numpy as np
from xicam.plugins import ProcessingPlugin, Input, Output
from scipy.ndimage import morphology


class ThresholdMaskPlugin(ProcessingPlugin):
    data = Input(description='Frame image data',
                 type=np.ndarray)
    minimum = Input(description='Threshold floor',
                    type=int)
    maximum = Input(description='Threshold ceiling',
                    type=int)
    neighborhood = Input(description='Neighborhood size in pixels for morphological opening. Only clusters of this size'
                                     ' that fail the threshold are masked',
                         type=int)
    mask = Output(description='Thresholded mask (1 is masked)',
                  type=np.ndarray)

    def evaluate(self):
        self.mask.value = np.logical_or(self.data.value < self.minimum.value, self.data.value > self.maximum.value)

        y, x = np.ogrid[-self.neighborhood.value:self.neighborhood.value + 1,
               -self.neighborhood.value:self.neighborhood.value + 1]
        kernel = x ** 2 + y ** 2 <= self.neighborhood.value ** 2

        morphology.binary_opening(self.mask.value, kernel, output=self.mask.value)  # write-back to mask
