from pyFAI import detectors
import numpy as np
from collections import OrderedDict


class FastCCD(detectors.Detector):
    aliases = ['Fast CCD']
    MAX_SHAPE = (1000, 960)

    def calc_mask(self):
        """
        Returns a generic mask for FastCCD detectors...
        """

        mask = np.zeros((1000, 960))
        # mask middle 19 rows
        mask[500 - 19 / 2:500 + 19 / 2, :] = 1
        # TODO: check that this mask is correct

        return mask


if __name__ == '__main__':
    assert detectors.ALL_DETECTORS['fastccd']
