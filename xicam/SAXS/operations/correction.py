import numpy as np
from numba import njit, prange
from typing import Iterable, Tuple
from xicam.plugins.operationplugin import operation, display_name, output_names, describe_input, \
    describe_output, categories, visible
import pyqtgraph as pg
from ..utils import get_label_array
from xarray import DataArray


def correct(array, flats, bkg, gain_map=(1, 2, 4, 8), clip=False):
    return _correct(np.asarray(array, dtype=np.uint16),
                    np.asarray(flats, dtype=np.uint16),
                    np.asarray(bkg, dtype=np.uint16),
                    clip=clip)


@njit(parallel=True)
def _correct(array, flats, bkg, gain_map=(1, 2, 4, 8), clip=False):
    # 16-bit unsigned
    # image: bits 0 - 12
    # bad:   bit 13
    # gain:  bits 14-15
    # gain1: 0b11 (3)
    # gain2: 0b10 (2)
    # gain8: 0b00 (0)
    masked_flat = 0x1FFF & flats
    masked_dark = 0x1FFF & bkg
    out = np.empty_like(array, dtype=np.int32)

    for i in prange(array.shape[0]):
        for j in prange(array.shape[1]):
            for k in prange(array.shape[2]):
                val = array[i, j, k]

                intensity = 0x1FFF & val
                bad_flag = 0x1 & (val >> 13)
                gain = gain_map[0x3 & (val >> 14)]

                bkg_gain = gain_map[0x3 & (bkg[j, k] >> 14)]

                out[i, j, k] = masked_flat[j, k] * gain * intensity

                if clip:
                    if intensity < masked_dark[j, k]:
                        out[i, j, k] = bkg_gain * masked_dark[j, k]

                if bad_flag:
                    out[i, j, k] = 0
                else:
                    out[i, j, k] -= bkg_gain * masked_dark[j, k]

    return out


def reduce_data(images, slices):
    trimmed_images = []
    for i in range(len(images)):
        image = np.asarray(images[i])
        image = image[slices]
        trimmed_images.append(image)
        del image

    return DataArray(np.asarray(trimmed_images))


@operation
@display_name('FastCCD Correction')
@describe_input('images', '3-dimensional input array containing 2-dimensional images')
@describe_input('flats', '2-dimensional input array containing flat image data')
@describe_input('darks', '3-dimensional input array containing 2-dimensional dark image data')
@describe_input('gains', 'n-dimensional input array containing gain values')
@output_names('images', 'labels')
@describe_output('images', 'Corrected fastccd image data')
@categories(('Scattering', 'Calibration'))
@visible('images', False)
@visible('flats', False)
@visible('darks', False)
def correct_fastccd_image(images: np.ndarray,
                          flats: np.ndarray = None,
                          darks: np.ndarray = None,
                          gains: tuple = (1, 2, 4, 8),
                          clip_below_dark: bool = False,
                          rois: Iterable[pg.ROI] = None,
                          image_item: pg.ImageItem = None,
                          ) -> Tuple[np.ndarray, np.ndarray]:
    # TODO: is this pulling from the correct dark? we need of mapping of gain index to dark array?

    if images.ndim not in [2, 3]:
        raise ValueError(f"\"images\" expects a 2- or 3-dimensional image array; shape = \"{images.shape}\"")

    flats = flats
    if flats is None:
        flats = np.ones_like(images[0])
    elif flats.ndim != 2:
        raise ValueError(f"\"flats\" should be 2-dimensional; shape = \"{flats.shape}\"")

    darks = darks
    if darks is None:
        darks = np.zeros_like(images[0])
    elif darks.ndim == 3:
        darks = np.sum(darks, axis=0) / darks.shape[0]
    elif darks.ndim == 2:
        pass  # darks is already a single frame

    labels = np.zeros((1, *images.shape[-2:]))
    if rois and image_item:
        labels = get_label_array(images, rois=rois, image_item=image_item)

        # Trim the image based on labels, and resolve to memory
        si, se = np.where(np.flipud(labels))
        # images = np.asarray(images[:, si.min():si.max() + 1, se.min():se.max() + 1])
        slices = slice(si.min(), si.max() + 1), slice(se.min(), se.max() + 1)
        template = DataArray(np.empty((images.shape[0], si.max() - si.min() + 1, se.max() - se.min() + 1))).chunk(
            images._variable.data.chunksize)
        images = images.map_blocks(reduce_data, template=template, kwargs=dict(slices=slices)).compute()

        flats = np.asarray(flats[si.min():si.max() + 1, se.min():se.max() + 1])
        darks = np.asarray(darks[si.min():si.max() + 1, se.min():se.max() + 1])
        labels = np.asarray(np.flipud(labels)[si.min():si.max() + 1, se.min():se.max() + 1])

    corrected_images = correct(images,
                               flats,
                               darks,
                               gains,
                               clip=clip_below_dark)
    return corrected_images, labels
