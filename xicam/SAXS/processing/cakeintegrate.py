from xicam.plugins.operationplugin import OperationPlugin, describe_input, display_name, \
                                          describe_output, output_names, categories
import numpy as np
from pyFAI import units
from pyFAI.azimuthalIntegrator import AzimuthalIntegrator

@OperationPlugin
@display_name('Integrate Cake')
@describe_input('azimuthal_integrator', ' PyFAI.AzimuthalIntegrator object')
@describe_input('data', 'Input array of two or more dimensions')
@describe_input('num_bin_q', 'Number of bins along q')
@describe_input('num_bin_chi', 'Number of bins along chi')
@describe_input('polarization_factor', 'Polarization factor for correction')
@describe_input('unit_q', 'requested output unit for q')
@describe_input('radial_range', 'The lower and upper range of the radial unit. \
                If not provided, range is simply (data.min(), data.max()). \
                Values outside the range are ignored.')
@describe_input('azimuthal_range', 'The lower and upper range of the azimuthal angle in degree. \
                If not provided, range is simply (data.min(), data.max()). \
                Values outside the range are ignored.')
@describe_input('mask', 'Array (same size as image) with 1 for masked pixels, and 0 for valid pixels')
@describe_input('dark', 'Dark noise image')
@describe_input('flat', 'Flat field image')
@describe_input('method', 'Can be "numpy", "cython", "BBox" or "splitpixel", "lut", "csr", "nosplit_csr", \
                "full_csr", "lut_ocl" and "csr_ocl" if you want to go on GPU. To Specify the device:\
                "csr_ocl_1,2"')
@describe_input('normalization_factor', 'Value of a normalization monitor')

@describe_output('cake', 'Binned/pixel-split integrated intensity')
@describe_output('chi', 'Chi bin center positions')
@describe_output('q', 'Q bin center positions')
@output_names('cake')
@output_names('chi')
@output_names('q')

@categories('Scattering', 'Integral')

def integrate_cake(azimuthal_integrator: AzimuthalIntegrator,
                   data: np.ndarray,
                   num_bin_q: int = 1000,
                   num_bin_chi: int= 1000,
                   polarization_factor: float= 0,
                   unit_q: [str, units.Unit] = 'q_A^-1',
                   radial_range: tuple,
                   azimuthal_range: tuple,
                   mask: np.ndarray,
                   dark: np.ndarray,
                   flat: np.ndarray,
                   method: str= 'splitbbox',
                   normalization_factor: float=  1) -> np.ndarray:

    cake, q, chi = azimuthal_integrator.integrate2d(data=nonesafe_flipud(data),
                                                            npt_rad=num_bin_q,
                                                            npt_azim=num_bin_chi,
                                                            radial_range=radial_range,
                                                            azimuth_range=azimuthal_range,
                                                            mask=nonesafe_flipud(mask),
                                                            polarization_factor=polarization_factor,
                                                            dark=nonesafe_flipud(dark),
                                                            flat=nonesafe_flipud(flat),
                                                            method=method,
                                                            unit=unit,
                                                            normalization_factor=normalization_factor)
    return cake, q, chi

def nonesafe_flipud(data: np.ndarray):
    if data is None: return None
    return np.flipud(data).copy()
