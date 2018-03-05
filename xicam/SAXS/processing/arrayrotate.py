from xicam.plugins import ProcessingPlugin, Input, Output, InOut
import numpy as np


class ArrayRotate(ProcessingPlugin):
    data = InOut(description='Array of two or more dimensions.', type=np.ndarray)
    k = Input(description='Number of times the array is rotated by 90 degrees.', type=int, default=1)
    axes = Input(description='The array is rotated in the plane defined by the axes. Axes must be different.',
                 type=np.ndarray, default=(0, 1))

    def evaluate(self):
        self.data.value = np.rot90(self.data.value, self.k.value, self.axes.value)
