from typing import Tuple

from xicam.core.intents import PlotIntent
from xicam.plugins.operationplugin import operation, output_names, display_name, describe_input, describe_output, \
    categories, intent
import numpy as np
from pyFAI.azimuthalIntegrator import AzimuthalIntegrator


@operation
@display_name("X Integration")
@output_names("q_x", "I")
@describe_input("azimuthal_integrator", 'A PyFAI.AzimuthalIntegrator object')
@describe_input("data", '2d array representing intensity for each pixel')
@describe_input("mask", 'Array (same size as image) with 1 for masked pixels, and 0 for valid pixels')
@describe_input('dark', 'Dark frame image')
@describe_input('flat', 'Flat field image')
@describe_input('normalization_factor', 'Value of a normalization monitor')
@describe_output('q_x', "q_x bin center positions")
@categories(('Scattering', 'Integration'))
@intent(PlotIntent, name='X Integration', output_map={'x': 'q_x', 'y': 'I'}, labels={'bottom': 'q_x', 'left': 'I'})
@describe_output('I', 'Binned/pixel-split integrated intensity')
def x_integrate(azimuthal_integrator: AzimuthalIntegrator,
                data: np.ndarray,
                mask: np.ndarray = None,
                dark: np.ndarray = None,
                flat: np.ndarray = None,
                normalization_factor: float = 1) -> Tuple[np.ndarray, np.ndarray]:
    if dark is None: dark = np.zeros_like(data)
    if flat is None: flat = np.ones_like(data)
    if mask is None: mask = np.zeros_like(data)
    I = np.sum((data - dark) * np.average(flat - dark) / (flat - dark) / normalization_factor * np.logical_not(mask),
               axis=0)
    centerx = azimuthal_integrator.getFit2D()['centerX']
    centerz = azimuthal_integrator.getFit2D()['centerY']
    q_x = azimuthal_integrator.qFunction(np.array([centerz] * data.shape[1]),
                                         np.arange(0, data.shape[1])) / 10.
    q_x[np.arange(0, data.shape[1]) < centerx] *= -1.

    return q_x, I
