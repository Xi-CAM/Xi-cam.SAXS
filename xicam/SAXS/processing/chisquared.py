from xicam.plugins import ProcessingPlugin, Input, Output
import numpy as np


class chisquared(ProcessingPlugin):
    dataA = Input(description='Frame A image data', type=np.ndarray)
    dataB = Input(description='Frame B image data', type=np.ndarray)

    chisquared = Output(description='Chi-squared difference between consecutive frames')

    def evaluate(self):
        self.chisquared.value = (self.dataA.value - self.dataB.value) ** 2.
