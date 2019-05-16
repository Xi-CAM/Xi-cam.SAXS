### Module example (ArrayRotate from Ron)

# from xicam.plugins import ProcessingPlugin, Input, Output, InOut
# import numpy as np


# class ArrayRotate(ProcessingPlugin):
#     data = InOut(description='Array of two or more dimensions.', type=np.ndarray)
#     k = Input(description='Number of times the array is rotated by 90 degrees.', type=int, default=1)
#     axes = Input(description='The array is rotated in the plane defined by the axes. Axes must be different.',
#                  type=np.ndarray, default=(0, 1))

#     def evaluate(self):
#         self.data.value = np.rot90(self.data.value, self.k.value, self.axes.value)

### Module from QZ starts here:

from xicam.plugins import ProcessingPlugin, Input, Output, InOut
from scipy import ndimage
import numpy as np


class CoM(ProcessingPlugin):
    data = Input(description='Array of two or more dimensions.', type=np.ndarray)
    mask = Input(description='Array (same size as image) with 1 for masked pixels, and 0 for valid pixels',
                 type=np.ndarray)
    x_min = Input(description='X pixel index, bottom left.', type=int, default=1)
    y_min = Input(description='Y pixel index, bottom left.', type=int, default=1)

    x_max = Input(description='X pixel index, top right.', type=int, default=1000)
    y_max = Input(description='Y pixel index, top right.', type=int, default=1000)

    x_cen = InOut(description='X pixel index, center of mass', type=float)
    y_cen = InOut(description='Y pixel index, center of mass', type=float)

    def evaluate(self):
        data = np.flipud(self.data.value)
        mask = np.flipud(self.mask.value)
        data = data * np.logical_not(mask)
        (self.y_cen.value, self.x_cen.value) = ndimage.measurements.center_of_mass(
            data[self.y_min.value:self.y_max.value,
            self.x_min.value:self.x_max.value])
        self.x_cen.value = self.x_cen.value + self.x_min.value
        self.y_cen.value = self.y_cen.value + self.y_min.value
