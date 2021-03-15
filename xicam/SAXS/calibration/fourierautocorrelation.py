import numpy as np
from scipy import signal
from xicam.plugins.operationplugin import operation, output_names, display_name, describe_input, describe_output, \
    categories
from pyFAI.azimuthalIntegrator import AzimuthalIntegrator
from typing import Tuple


@operation
@output_names('beam_center', 'azimuthal_integrator')
@display_name('Fourier Autocorrelation')
@describe_input('data', "SAXS/WAXS calibrant image data")
@describe_input('azimuthal_integrator', "The `AzimuthalIntegrator` to modify; center will be modified in place")
@describe_output('beam_center', "Approximated position of the direct beam center")
@describe_output('azimuthal_integrator',
                 "The input `AzimuthalIntegrator` with its center shifted to the estimated center. If not provided, then `None`.")
@categories(('Scattering', 'Calibration'))
def fourier_autocorrelation(data: np.ndarray, azimuthal_integrator: AzimuthalIntegrator = None) -> \
        Tuple[Tuple[float, float], AzimuthalIntegrator]:
    """
    Estimate beam center of a SAXS/WAXS image using fourier autocorrelation. The validity of this technique depends on
    having negligible camera tilt/rotation, and a significant fraction of at least one ring feature.

    Parameters
    ----------
    data: np.ndarray
        SAXS/WAXS calibrant image data
    azimuthal_integrator: Optional[AzimuthalIntegrator]
        The `AzimuthalIntegrator` to modify; center will be modified in place

    Returns
    -------
    Tuple[float]
        Approximated position of the direct beam center
    Union[AzimuthalIntegrator, None]
        The input `AzimuthalIntegrator` with its center shifted to the estimated center. If not provided, then `None`.

    """

    mask = azimuthal_integrator.detector.mask
    data = np.squeeze(np.asarray(data))
    if mask is not None and mask.shape == data.shape:
        data = data * (1 - mask)

    # slice into the first index as long as there's higher dimensionality
    while len(data.shape) > 2:
        data = data[0]

    con = signal.fftconvolve(data, data) / np.sqrt(
        signal.fftconvolve(np.ones_like(data), np.ones_like(data)))

    center = np.array(np.unravel_index(con.argmax(), con.shape)) / 2.
    fit2dparams = azimuthal_integrator.getFit2D()
    fit2dparams['centerX'] = center[1]
    fit2dparams['centerY'] = center[0]
    azimuthal_integrator.setFit2D(**fit2dparams)

    return center, azimuthal_integrator
