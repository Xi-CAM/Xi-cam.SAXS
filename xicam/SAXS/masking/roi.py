from typing import Iterable

from xicam.SAXS.utils import get_label_array
from xicam.plugins.operationplugin import operation, output_names, display_name, describe_input, describe_output, \
    categories
from pyFAI.integrator.azimuthal import AzimuthalIntegrator
import numpy as np
import pyqtgraph as pg


@operation
@display_name("ROI selection")
@describe_input('azimuthal_integrator', "The `AzimuthalIntegrator` to including a detector instance describing the camera hardware.")
@describe_output("mask", "The calculated mask derived from the detector's profile. (1 is masked)")
@output_names("roi_mask")
@categories(("Scattering", "Masking"))
def roi_mask_plugin(data: np.array = None,
                    rois: Iterable[pg.ROI] = None,
                    geometry: AzimuthalIntegrator = None,
                    image_item: pg.ImageItem = None,
                    mask: np.ndarray = None) -> np.ndarray:
    if rois:
        labels = get_label_array(data, rois=rois, image_item=image_item, geometry=geometry)
        return np.logical_or(mask, np.logical_not(labels))
    else:
        return mask
