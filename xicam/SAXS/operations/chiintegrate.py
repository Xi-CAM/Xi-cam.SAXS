from typing import Union, Tuple

from xicam.core.intents import PlotIntent
from xicam.plugins.operationplugin import operation, output_names, display_name, describe_input, describe_output, \
    categories, intent
import numpy as np
from pyFAI import units
from pyFAI.azimuthalIntegrator import AzimuthalIntegrator


@operation
@output_names("chi", "I")
@display_name("Chi Integration")
@describe_input("azimuthal_integrator", 'A PyFAI.AzimuthalIntegrator object')
@describe_input("data", '2d array representing intensity for each pixel')
@describe_input("npt_azim", 'Number of bins along chi')
@describe_input("polz_factor", 'Polarization factor for correction')
@describe_input("unit", 'Output units for q')
@describe_input("radial_range", 'The lower and upper range of the radial unit. If not provided, range is simply '
                                '(data.min(), data.max()). Values outside the range are ignored.')
@describe_input("azimuth_range", 'The lower and upper range of the azimuthal angle in degree. If not provided, '
                                 'range is simply (data.min(), data.max()). Values outside the range are ignored.')
@describe_input("mask", 'Array (same size as image) with 1 for masked pixels, and 0 for valid pixels')
@describe_input("dark", 'Dark noise image')
@describe_input("flat", 'Flat field image')
@describe_input("method", 'Can be "numpy", "cython", "BBox" or "splitpixel", "lut", "csr", "nosplit_csr", '
                          '"full_csr", "lut_ocl" and "csr_ocl" if you want to go on GPU. To Specify the device: '
                          '"csr_ocl_1,2"')
@describe_input('normalization_factor', 'Value of a normalization monitor')
@describe_output("chi", 'Q bin center positions')
@describe_output("I", 'Binned/pixel-split integrated intensity')
@intent(PlotIntent, name="Chi Integrate", output_map={"x": "chi", "y": "I"}, labels={"bottom": "chi", "left": "I"})
@categories(("Scattering", "Integration"))
def chi_integrate(azimuthal_integrator: AzimuthalIntegrator,
                  data: np.ndarray,
                  npt_azim: int = 1000,
                  polz_factor: float = 0,
                  unit: Union[str, units.Unit] = "q_A^-1",
                  radial_range: Tuple[float, float] = None,
                  azimuth_range: Tuple[float, float] = None,
                  mask: np.ndarray = None,
                  dark: np.ndarray = None,
                  flat: np.ndarray = None,
                  method: str = 'splitbbox',
                  normalization_factor: float = 1, ) -> Tuple[np.ndarray, np.ndarray]:
    I, q, chi = azimuthal_integrator.integrate2d(data=data,
                                                 npt_rad=1,
                                                 npt_azim=npt_azim,
                                                 radial_range=radial_range,
                                                 azimuth_range=azimuth_range,
                                                 mask=mask,
                                                 polarization_factor=polz_factor,
                                                 dark=dark,
                                                 flat=flat,
                                                 method=method,
                                                 unit=unit,
                                                 normalization_factor=normalization_factor)

    I = np.sum(I, axis=1)
    return I, chi

# def nonesafe_flipud(data: np.ndarray):
#     if data is None: return None
#     return np.flipud(data).copy()
