import numpy as np
from xicam.plugins.operationplugin import operation, output_names, display_name, categories


@operation
@output_names('diffusion_coefficient')
@display_name('Diffusion Coefficient')
@categories(('XPCS',))
def diffusion_coefficient(roi_q: np.ndarray, relaxation_rates: np.ndarray):
    return np.average(relaxation_rates / roi_q ** 2)
