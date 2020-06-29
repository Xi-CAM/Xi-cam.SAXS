from xicam.plugins.operationplugin import operation, output_names, display_name, describe_input, describe_output, \
    categories
from pyFAI import calibrant
from pyFAI.azimuthalIntegrator import AzimuthalIntegrator
import numpy as np


@operation
@display_name('Simulate Calibrant')
@output_names('data')
@describe_output('data', 'Simulated calibrant image data')
@describe_input('calibrant', "Calibrant standard record")
@describe_input('azimuthal_integrator', "Azimuthal integrator; the SDD will be modified in-place")
@describe_input('I_max', 'Maximum intensity of rings')
@categories(('Scattering', 'Calibration'))
def simulate_calibrant(azimuthal_integrator: AzimuthalIntegrator,
                       calibrant: calibrant.Calibrant,
                       I_max: float = 1) -> np.ndarray:
    calibrant.set_wavelength(azimuthal_integrator.get_wavelength())
    data = calibrant.fake_calibration_image(azimuthal_integrator, Imax=I_max)

    return data
