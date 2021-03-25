import numpy as np
from astropy.modeling import Fittable1DModel, Parameter, fitting, models
from xicam.SAXS.patches.pyFAI import AzimuthalIntegrator
from xicam.SAXS.utils import average_q_from_labels
from xicam.core import msg
from xicam.core.intents import PlotIntent, ScatterIntent
from xicam.plugins.operationplugin import operation, output_names, display_name, categories, intent, visible


@operation
@output_names('diffusion_fit', 'x', 'diffusion_values', )
@display_name('Diffusion Coefficient')
@categories(('XPCS',))
@intent(PlotIntent, 'Linear fit of Diffusion',
        output_map={'x': 'x', 'y': 'diffusion_fit'},
        labels={'bottom': '\\frac{1}{q^2}', 'left': 'Diffusion Coefficient'},
        match_key='diffusion_coefficient')
@intent(ScatterIntent,
        'Diffusion Coefficients',
        output_map={'x': 'x', 'y': 'diffusion_values'},
        labels={'bottom': '\\frac{1}{q^2}', 'left': 'Diffusion Coefficient'},
        match_key='diffusion_coefficient')
@visible('labels', False)
@visible('relaxation_rates', False)
@visible('geometry', False)
def diffusion_coefficient(relaxation_rates: np.ndarray, labels: np.ndarray, geometry: AzimuthalIntegrator = None):
    if geometry is None:
        msg.notifyMessage('Calibrate required for diffusion coefficients.')

    qs = np.asarray(average_q_from_labels(labels, geometry))

    x = 1. / qs ** 2
    diffusion_values = relaxation_rates * x

    model = models.Linear1D()
    fitting_algorithm = fitting.LinearLSQFitter()

    fit = fitting_algorithm(model, x, diffusion_values)

    return fit(x), x, diffusion_values
