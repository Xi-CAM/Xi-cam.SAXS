from camsaxs import cwt2d
from typing import Tuple
import numpy as np
from xicam.plugins.operationplugin import operation, output_names, display_name, describe_input, describe_output, \
    categories


@operation
@output_names('center')
@display_name("Ricker Wavelet Calibration")
@describe_input("data", 'Calibrant frame image data')
@describe_input("domain", 'Search domain in pixels: (r_min, r_max)')
@describe_input("width", 'Approximate width of the calibrant ring in pixels')
@describe_output("center", "The position in pixels of the approximated beam center")
@categories(("Scattering", "Calibration"))
def ricker_wavelet(data: np.ndarray, domain: Tuple[float], width: float = 5) -> Tuple[float]:
    center, _ = cwt2d(data, domain=domain, width=width)
    return center
