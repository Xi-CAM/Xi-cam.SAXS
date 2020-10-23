import numpy as np
from xicam.plugins.operationplugin import operation, display_name, output_names, describe_input, \
    describe_output, categories, visible


@operation
@display_name('FastCCD Correction')
@describe_input('images', '3-dimensional input array containing 2-dimensional images')
@describe_input('flats', '2-dimensional input array containing flat image data')
@describe_input('darks', '3-dimensional input array containing 2-dimensional dark image data')
@describe_input('gains', 'n-dimensional input array containing gain values')
@output_names('corrected_images')
@describe_output('corrected_images', 'Corrected fastccd image data')
@categories(('Scattering', 'Calibration'))
@visible('images', False)
@visible('flats', False)
@visible('darks', False)
def correct_fastccd_image(images: np.ndarray,
                          flats: np.ndarray = None,
                          darks: np.ndarray = None,
                          gains: tuple = (1, 2, 4, 8)) -> np.ndarray:

    def correct(array, flats, bkg, gain_map=(1, 2, 4, 8)):
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
        gain_map = dict(zip((0, 1, 2, 3), gain_map))
        gain = np.vectorize(gain_map.get)(gain)
        # gain = np.vectorize(partial(lambda a, b: a[int((b + 1) / 2)], gain_map))(gain)
        arr = flats * gain * intensity
        arr = np.where(arr < bkg, bkg, arr)
        return np.array((1 - bad_flag) * (arr - bkg), dtype=np.uint16)

    # TODO: is this pulling from the correct dark? we need of mapping of gain index to dark array?

    if images.ndim not in [2, 3]:
        raise ValueError(f"\"images\" expects a 2- or 3-dimensional image array; shape = \"{images.shape}\"")

    flats = flats
    if flats is None:
        flats = 1
    elif flats.ndim != 2:
        raise ValueError(f"\"flats\" should be 2-dimensional; shape = \"{flats.shape}\"")

    darks = darks
    if darks is None:
        darks = 0
    elif darks.ndim != 3:
        raise ValueError(f"\"darks\" should be 3-dimensional; shape = \"{darks.shape}\"")
    else:
        darks = np.sum(darks, axis=0) / darks.shape[0]

    corrected_images = correct(np.asarray(images, dtype=np.uint16),
                               np.asarray(flats, dtype=np.float32),
                               np.asarray(darks, dtype=np.float32),
                               gains)
    return corrected_images

