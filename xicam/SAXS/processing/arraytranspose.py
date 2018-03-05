from xicam.plugins import ProcessingPlugin, Input, Output, InOut
import numpy as np


class ArrayTranspose(ProcessingPlugin):
    data = InOut(description='Input array.', type=np.ndarray)
    axes = Input(
        description='By default, reverse the dimensions, otherwise permute the axes according to the values given.',
        type=np.array)

    def evaluate(self):
        self.data.value = np.transpose(self.data.value, self.axes.value)
