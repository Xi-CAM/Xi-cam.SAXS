from typing import Tuple

from xicam.core.intents import PlotIntent
from xicam.plugins.operationplugin import operation, output_names, display_name, describe_input, describe_output, \
    categories, intent
import numpy as np
from pyFAI.integrator.azimuthal import AzimuthalIntegrator


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
    if data.ndim == 2:
        data = [data]
    if dark is None: dark = np.zeros_like(data[0])
    if flat is None: flat = np.ones_like(data[0])
    if mask is None: mask = np.zeros_like(data[0])
    I = []
    q_x = []
    for frame in data:
        frame = np.asarray(frame)
        I_i = np.sum((frame - dark) * np.average(flat - dark) / (flat - dark) / normalization_factor * np.logical_not(mask),
                     axis=-2)
        I.append(I_i)
        centerx = azimuthal_integrator.getFit2D()['centerX']
        centerz = azimuthal_integrator.getFit2D()['centerY']
        q_x_i = azimuthal_integrator.qFunction(np.array([centerz] * frame.shape[-1]),
                                               np.arange(0, frame.shape[-1])) / 10.
        q_x_i[np.arange(0, frame.shape[-1]) < centerx] *= -1.
        q_x.append(q_x_i)

        # TODO: support dynamic q
    return np.asarray(q_x_i), np.asarray(I)
