from xicam.plugins.operationplugin import OperationPlugin, describe_input, display_name, \
                                          describe_output, output_names, categories
import numpy as np
from pyFAI import units
from pyFAI.azimuthalIntegrator import AzimuthalIntegrator



@OperationPlugin
@dispay_name('Intgreate Chi')
@describe_input('azimuthal_integrator', ' PyFAI.AzimuthalIntegrator object')
@describe_input('data', 'Input array of two or more dimensions')
@describe_input('num_bin_chi', 'Number of bins along chi')
@describe_input('polarization_factor', 'Polarization factor for correction')
@describe_input('unit_chi', 'requested output unit for chi')
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


@describe_output('I_chi', 'Binned/pixel-split integrated intensity')
@describe_output('chi', 'Chi bin center positions')
@describe_output('q', 'q bin center positions')
@output_names('I_chi')
@output_names('chi')
@output_names('q')

@categories('Scattering', 'Integral')

def integrate_cake(azimuthal_integrator: AzimuthalIntegrator,
                   data: np.ndarray,
                   num_bin_chi: int= 1000,
                   polarization_factor: float= 0,
                   unit_chi: [str, units.Unit] = '2th_rad',
                   radial_range: tuple,
                   azimuthal_range: tuple,
                   mask: np.ndarray,
                   dark: np.ndarray,
                   flat: np.ndarray,
                   method: str= 'splitbbox',
                   normalization_factor: float=  1) -> np.ndarray:

    I_chi, q, chi = azimuthal_integrator.integrate2d(data=nonesafe_flipud(data),
                                                            npt_rad=1,
                                                            npt_azim=num_bin_chi,
                                                            radial_range=radial_range,
                                                            azimuth_range=azimuthal_range,
                                                            mask=nonesafe_flipud(mask),
                                                            polarization_factor=polarization_factor,
                                                            dark=nonesafe_flipud(dark),
                                                            flat=nonesafe_flipud(flat),
                                                            method=method,
                                                            unit=unit_chi,
                                                            normalization_factor=normalization_factor)
    return I_chi, q, chi

# NOTE: notesafe_flipup exist in cakeintegrate too, remove duplicate?
def nonesafe_flipud(data: np.ndarray):
    if data is None: return None
    return np.flipud(data).copy()
