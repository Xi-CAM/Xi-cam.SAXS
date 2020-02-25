from functools import partial

import numpy as np

from xicam.core import msg
from xicam.plugins import ProcessingPlugin, Input, Output


class CorrectImage(ProcessingPlugin):
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


try:
    from csxtools.fastccd import correct_images
    from csxtools.utils import stackmean
    import numpy as np
    from xicam.plugins.processingplugin import Input, Output, ProcessingPlugin


    class CSXCorrectImage(ProcessingPlugin):
        """Subtract backgrond and gain correct images
        This routine subtrtacts the backgrond and corrects the images
        for the multigain FastCCD ADC.
        Parameters
        ----------
        in : array_like
            Input array of images to correct of shape (N, y, x)  where N is the
            number of images and x and y are the image size.
        dark : array_like, optional
            Input array of dark images. This should be of shape (3, y, x).
            dark[0] is the gain 8 (most sensitive setting) dark image with
            dark[2] being the gain 1 (least sensitive) dark image.
        flat : array_like, optional
            Input array for the flatfield correction. This should be of shape
            (y, x)
        gain : tuple, optional
            These are the gain multiplication factors for the three different
            gain settings
        Returns
        -------
        array_like
            Array of corrected images of shape (N, y, x)
        """
        # Images are expected to be of type np.uint16 (csxtools.utils.py:94)
        bitmasked_images = Input(description="", type=np.ndarray, visible=False)
        # Darks are expected to be of type np.float32 (csxtools.fastccd.images.py:43)
        dark_images = Input(description="", type=np.ndarray, visible=False)
        # Flats are expected to be of type np.float32 (csxtools.fastccd.images.py:47)
        flat_field = Input(description="", type=np.ndarray, default=None, visible=False)
        gain = Input(description="", type=tuple, visible=False)

        corrected_images = Output(description="", type=np.ndarray)

        def evaluate(self):
            data = np.asarray(self.bitmasked_images.value.astype(np.uint16))
            kwargs = dict()
            reduced_dark_image = self.dark_images.value
            if reduced_dark_image is not None:
                reduced_dark_image = stackmean(np.asarray(self.dark_images.value, dtype=np.float32))
                darks = np.array([reduced_dark_image,
                                  np.zeros(shape=reduced_dark_image.shape),
                                  np.zeros(shape=reduced_dark_image.shape)],
                                 dtype=np.float32)
                kwargs['dark'] = darks
            if self.flat_field.value is not None:
                kwargs['flat'] = self.flat_field.value.astype(np.float32)
            if self.gain.value is not None:
                kwargs['gain'] = self.gain.value
            self.corrected_images.value = correct_images(data, **kwargs)
except ImportError:
    msg.logMessage("Cannot import csxtools; will not be tested against.")


if __name__ == "__main__":
    shape = (5, 5)
    dtype = np.float32
    low = np.zeros(shape=shape, dtype=dtype)
    high = np.ones(shape=shape, dtype=dtype) * 100
    raw_images = np.array([low, high], dtype=np.uint16)
    dark_image1 = np.zeros(shape=shape)
    dark_image1[0] = 1
    dark_image2 = np.zeros(shape=shape)
    dark_image2[:, 3] = 1
    dark_images = np.array([dark_image1, dark_image2], dtype=dtype)
    print(f"dark images shape: {dark_images.shape}")
    rr = stackmean(dark_images)
    print(type(rr))
    print(f"low:\n{low}")
    print()
    print(f"high:\n{high}")
    print()
    print(f"darks:\n{dark_images}")
    print()
    print("reduced dark image")
    print(rr)
    print()
    print("corrected")

    darks = np.array([
        rr,
        np.zeros(shape=rr.shape),
        np.zeros(shape=rr.shape), ],
        dtype=dtype)
    corrected = correct_images(images=raw_images, dark=darks)
    print(corrected)

    print()
    print('-' * 80)
