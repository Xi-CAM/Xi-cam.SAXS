from functools import partial

import numpy as np

from xicam.plugins import ProcessingPlugin, Input, Output


class CorrectFastCCDImage(ProcessingPlugin):
    images = Input(name="image", type=np.ndarray)
    flats = Input(name="flats", type=np.ndarray)
    darks = Input(name="darks", type=np.ndarray)
    gains = Input(name="gains", type=tuple, default=(1, 4, 8))
    corrected_images = Output(name="corrected_images", type=np.ndarray)

    def evaluate(self):
        def correct(array, flats, bkg, gain_map=(1, 4, 8)):
            # 16-bit unsigned
            # image: bits 0 - 12
            # bad:   bit 13
            # gain:  bits 14-15
            # gain1: 0b11 (3)
            # gain2: 0b10 (2)
            # gain8: 0b00 (0)
            intensity = np.bitwise_and(0x1FFF, array)
            bad_flag = np.bitwise_and(0x1, np.right_shift(array, 13))
            gain = np.bitwise_and(0x3, np.right_shift(array, 14))
            # map the gain bit values to the gain map indices to get the actual gain values
            # e.g. 3 -> index 2; 2 -> index 1; 1 -> index 0
            gain = np.vectorize(partial(lambda a, b: a[int((b + 1) / 2)], gain_map))(gain)
            arr = flats * gain * intensity
            arr = np.where(arr < bkg, bkg, arr)
            return np.array((1 - bad_flag) * (arr - bkg), dtype=np.uint16)

        if self.images.value.ndim != 3:
            raise ValueError(f"\"images\" expects a 3-dimensional image array; shape = \"{self.images.value.shape}\"")

        flats = self.flats.value
        if flats is None:
            flats = np.ones(self.images.value.shape[1:])
        if flats.ndim != 2:
            raise ValueError(f"\"flats\" should be 2-dimensional; shape = \"{self.flats.value.shape}\"")

        darks = self.darks.value
        if darks is None:
            darks = np.zeros(self.images.value.shape)
        if darks.ndim != 3:
            raise ValueError(f"\"darks\" should be 3-dimensional; shape = \"{self.darks.value.shape}\"")

        darks = np.sum(darks, axis=0) / darks.shape[0]
        self.corrected_images.value = correct(np.asarray(self.images.value, dtype=np.uint16),
                                              np.asarray(flats, dtype=np.float32),
                                              np.asarray(darks, dtype=np.float32),
                                              self.gains.value)
