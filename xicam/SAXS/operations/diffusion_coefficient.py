import numpy as np
from astropy.modeling import Fittable1DModel, Parameter, fitting, models
from xicam.SAXS.patches.pyFAI import AzimuthalIntegrator
from xicam.SAXS.utils import average_q_from_labels
from xicam.core import msg
from xicam.core.intents import PlotIntent, ScatterIntent
from xicam.plugins.operationplugin import operation, output_names, display_name, categories, intent, visible


@operation
@output_names('diffusion_fit', 'x', 'relaxation_rates', 'g2', 'tau', 'fit_curve')
@display_name('Diffusion Coefficient')
@categories(('XPCS',))
@intent(PlotIntent, 'Linear fit of Diffusion',
        output_map={'x': 'x', 'y': 'diffusion_fit'},
        labels={'bottom': 'q²', 'left': 'Γ'},
        match_key='diffusion_coefficient',
        mixins=["ToggleSymbols"])
@intent(ScatterIntent,
        'Diffusion Coefficients',
        output_map={'x': 'x', 'y': 'relaxation_rates'},
        labels={'bottom': 'q²', 'left': 'Γ'},
        match_key='diffusion_coefficient',
        mixins=["ToggleSymbols"])
# Make sure g2 and its fit intents are propagated to this end operation
@intent(PlotIntent,
        match_key='1-time Correlation',
        name='g2',
        yLog=True,
        labels={"bottom": "𝜏", "left": "g₂"},
        output_map={'x': 'tau', 'y': 'g2'},
        mixins=["ToggleSymbols"])
@intent(PlotIntent,
        canvas_name="1-time Correlation",
        match_key='1-time Correlation',
        name='g2 fit',
        labels={"bottom": "𝜏", "left": "g₂"},
        output_map={'x': 'tau', 'y': 'fit_curve'},
        mixins=["ToggleSymbols"])
@visible('labels', False)
@visible('relaxation_rates', False)
@visible('g2', False)
@visible('tau', False)
@visible('fit_curve', False)
@visible('geometry', False)
@visible('transmission_mode', False)
@visible('incidence_angle', False)
def diffusion_coefficient(relaxation_rates: np.ndarray,
                          labels: np.ndarray,
                          g2: np.ndarray,
                          tau: np.ndarray,
                          fit_curve: np.ndarray,
                          geometry: AzimuthalIntegrator = None,
                          transmission_mode: str = 'transmission',
                          incidence_angle: float = None,
                          ):
    # TODO: what should we do when we only get one relaxation rate (ie one roi / non-segmented roi)
    if geometry is None:
        msg.notifyMessage('Calibrate required for diffusion coefficients.')
        
        return np.array([0]), np.array([0]), relaxation_rates, g2, tau, fit_curve
        
    else:
        qs = np.asarray(average_q_from_labels(labels, geometry, transmission_mode, incidence_angle))

        x = qs ** 2
        # diffusion_values = relaxation_rates / x

        model = models.Linear1D()
        fitting_algorithm = fitting.LinearLSQFitter()

        fit = fitting_algorithm(model, x, relaxation_rates)

        return fit(x), x, relaxation_rates, g2, tau, fit_curve
