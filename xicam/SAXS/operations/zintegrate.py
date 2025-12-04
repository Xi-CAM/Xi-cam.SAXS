from typing import Tuple

from xicam.core.intents import PlotIntent
from xicam.plugins.operationplugin import operation, output_names, display_name, describe_input, describe_output, \
    categories, intent
import numpy as np
from pyFAI.integrator.azimuthal import AzimuthalIntegrator


@operation
@output_names("q_z", "I")
@display_name("Z Integration")
@describe_input("azimuthal_integrator", 'A PyFAI.AzimuthalIntegrator object')
@describe_input("data", '2d array representing intensity for each pixel')
@describe_input("mask", 'Array (same size as image) with 1 for masked pixels, and 0 for valid pixels')
@describe_input("dark", "Dark noise image")
@describe_input("flat", "Flat field image")
@describe_input("normalization_factor", 'Value of normalization monitor')
@describe_output("q", 'q_z bin center positions')
@describe_output("I", "Binned/pixel-split integrated intensity")
@categories(("Scattering", "Integration"))
@intent(PlotIntent, name="Z Integration", output_map={'x': 'q_z', 'y': 'I'}, labels={"bottom": "q_z", "left": "I"})
def z_integrate(azimuthal_integrator: AzimuthalIntegrator,
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
    q_z = []
    for frame in data:
        frame = np.asarray(frame)
        I_i = np.sum((frame - dark) * np.average(flat - dark) / (
                flat - dark) / normalization_factor * np.logical_not(mask), axis=-1)[::-1]
        I.append(I_i)
        centerx = azimuthal_integrator.getFit2D()['centerX']
        centerz = azimuthal_integrator.getFit2D()['centerY']
        q_z_i = azimuthal_integrator.qFunction(np.arange(0, frame.shape[-2]),
                                               np.array([centerx] * frame.shape[-2])) / 10
        q_z_i[np.arange(0, frame.shape[-2]) < centerz] *= -1.
        q_z_i = q_z_i[::-1]
        q_z.append(q_z_i)

        # TODO: support dynamic q

    return np.asarray(q_z_i), np.asarray(I)
