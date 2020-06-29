from xicam.plugins.operationplugin import operation, output_names, display_name, describe_input, describe_output, \
    categories
from pyFAI.azimuthalIntegrator import AzimuthalIntegrator
import numpy as np


@operation
@display_name("Detector Mask")
@describe_input('azimuthal_integrator', "The `AzimuthalIntegrator` to including a detector instance describing the camera hardware.")
@describe_output("mask", "The calculated mask derived from the detector's profile. (1 is masked)")
@output_names("mask")
@categories(("Scattering", "Masking"))
def detector_mask_plugin(azimuthal_integrator: AzimuthalIntegrator = None, mask:np.ndarray = None) -> np.ndarray:
    if azimuthal_integrator and azimuthal_integrator.detector:
        if mask is None:
            mask = np.zeros(azimuthal_integrator.detector.shape)
        mask = np.logical_or(azimuthal_integrator.detector.calc_mask(), mask)
        return mask
