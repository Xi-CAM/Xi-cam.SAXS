from pyFAI import detectors
import numpy as np
from collections import OrderedDict


class FastCCD(detectors.Detector):
    aliases = ['Fast CCD']
    MAX_SHAPE = (960, 2050)

    def __init__(self, pixel1=30.e-6, pixel2=30.e-6, max_shape=MAX_SHAPE):
        super(FastCCD, self).__init__(pixel1=pixel1, pixel2=pixel2, max_shape=max_shape)

    def calc_mask(self):
        """
        Returns a generic mask for FastCCD detectors...
        """

        mask = np.zeros(MAX_SHAPE)
        # mask middle 19 cols
        # TODO: fix overscanned pixels at IOC instead of this 19 col mask here
        mask[:, 2050 // 2 - 9: 2050 // 2 + 9] = 1
        # TODO: check that this mask is correct

        return mask


class LAMBDA(detectors.Detector):
    aliases = ['LAMBDA']
    MAX_SHAPE = (1536, 512)

    def __init__(self, pixel1=22.e-6, pixel2=22.e-6, max_shape=MAX_SHAPE):
        super(LAMBDA, self).__init__(pixel1=pixel1, pixel2=pixel2, max_shape=max_shape)


if __name__ == '__main__':
    assert detectors.ALL_DETECTORS['fastccd']
