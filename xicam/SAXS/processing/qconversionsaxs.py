from xicam.core.intents import PlotIntent
from xicam.plugins.operationplugin import operation, output_names, display_name, describe_input, describe_output, \
    categories, intent
import numpy as np
from pyFAI.azimuthalIntegrator import AzimuthalIntegrator


@operation
@display_name('SAXS q conversion')
@output_names('q_x', 'q_z')
@describe_input('integrator', 'A PyFAI.AzimuthalIntegrator object')
@describe_input('data', 'Frame image data')
@describe_output('q_x', 'q_x array with dimension of data')
@describe_output('q_y', 'q_y array with dimension of data')
@intent(PlotIntent, name='SAXS q conversion', output_names={'q_x': 'x', 'q_z': 'y'}, labels={'bottom': 'q_x',
                                                                                             'left': 'q_z'})
@categories(('Scattering', 'Transformations'))
def q_conversion_saxs(integrator: AzimuthalIntegrator,
                      data: np.ndarray) -> np.ndarray:
    chi = integrator.chiArray()
    twotheta = integrator.twoThetaArray()

    # TODO: Doble check what is chi = 0
    q_x = 2 * np.pi / integrator.getvalue('Wavelength') * np.sin(twotheta) * np.sin(chi)
    q_z = 2 * np.pi / integrator.getvalue('Wavelength') * np.sin(twotheta) * np.cos(chi)

    return q_x, q_z
