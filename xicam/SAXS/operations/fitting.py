import numpy as np
import skbeam.core.correlation as corr
from astropy.modeling import Fittable1DModel, Parameter, fitting
from xicam.core.intents import PlotIntent

from xicam.plugins.operationplugin import operation, output_names, display_name, describe_input, describe_output, \
    categories, intent, visible
from typing import Union, Tuple


@operation
@display_name('Fit Scattering Factor')
@output_names('fit_curve', 'relaxation_rates', "tau", "g2")
@describe_input('g2', 'Normalized intensity-intensity time autocorrelation')
@describe_input('tau', 'delay time')
@describe_input('beta', 'Optical contrast (speckle contrast), a sample-independent beamline parameter')
@describe_input('baseline', 'baseline of one time correlation equal to one for ergodic samples')
@describe_input('correlation_threshold', 'threshold defining which g2 values to fit')
@describe_output('fit_curve', 'Fitted model of the g2 curve')
@describe_output('relaxation_rates', 'Relaxation time associated with the samples dynamics')
@intent(PlotIntent,
        canvas_name="1-time Correlation",
        match_key='1-time Correlation',
        name='g2 fit',
        labels={"bottom": "𝜏", "left": "g₂"},
        output_map={'x': 'tau', 'y': 'fit_curve'},
        mixins=["ToggleSymbols"])
@intent(PlotIntent,
        canvas_name="1-time Correlation",
        match_key='1-time Correlation',
        name='g2',
        labels={"bottom": "𝜏", "left": "g₂"},
        output_map={'x': 'tau', 'y': 'g2'},
        mixins=["ToggleSymbols"])
@categories(('Scattering', 'Fitting'))
@visible('g2', False)
@visible('tau', False)
def fit_scattering_factor(g2: np.ndarray,
                          tau: np.ndarray,
                          beta: float = 1.0,
                          baseline: float = 1.0,
                          relaxation_rate: float = 0.01,
                          correlation_threshold: float = 2) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    model = ScatteringModel(beta, baseline, relaxation_rate=relaxation_rate)
    fitting_algorithm = fitting.SLSQPLSQFitter()
    threshold = min(len(tau), np.argmax(g2 < correlation_threshold))

    if g2.ndim > 1:
        fits = [fitting_algorithm(model, tau[:threshold], g2[i][:threshold]) for i in range(len(g2))]
    else:
        fits = [fitting_algorithm(model, tau[:threshold], g2[:threshold])]

    relaxation_rates = np.asarray([fit.relaxation_rate.value for fit in fits]).squeeze()
    fit_curves = np.asarray([fit(tau) for fit in fits]).squeeze()

    return fit_curves, relaxation_rates, tau, g2

    # labels = {'left': ['g<sub>2</sub>(&tau;)', 's'],
    #             'bottom': ['&tau;', 's']}
    # one_time_hint = PlotHint(self.lag_steps.value[1:], self.g2.value[1:], name="1-Time", labels=labels, xLog=True, style=Qt.SolidLine)
    # fit_hint = PlotHint(self.lag_steps.value[1:], self.fit_curve.value[1:], name="1-Time Fit", labels=labels, xLog=True, style=Qt.DashLine)
    # self.intents = [CoPlotHint(one_time_hint, fit_hint, name="1-Time")]


class ScatteringModel(Fittable1DModel):
    inputs = ('tau',)
    outputs = ('g2',)

    relaxation_rate = Parameter()

    def __init__(self, beta, baseline=1.0, **kwargs):
        self.beta = beta
        self.baseline = baseline
        super(ScatteringModel, self).__init__(**kwargs)

    def evaluate(self, tau, relaxation_rate):
        return corr.auto_corr_scat_factor(tau, self.beta, relaxation_rate, self.baseline)

    def fit_deriv(self, tau, relaxation_rate):
        d_relaxation_rate = -2 * self.beta * relaxation_rate * np.exp(-2 * relaxation_rate * tau)
        return [d_relaxation_rate]
