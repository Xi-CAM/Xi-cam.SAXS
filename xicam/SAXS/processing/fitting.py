import numpy as np
import skbeam.core.correlation as corr
from astropy.modeling import Fittable1DModel, Parameter, fitting
from xicam.core.intents import PlotIntent

from xicam.plugins.hints import CoPlotHint, PlotHint
from xicam.plugins.operationplugin import operation, output_names, display_name, describe_input, describe_output, \
    categories, intent
from typing import Union, Tuple


@operation
@display_name('Fit Scattering Factor')
@output_names('fit_curve', 'relaxation_rate')
@describe_input('g2', 'Normalized intensity-intensity time autocorrelation')
@describe_input('tau', 'delay time')
@describe_input('beta', 'Optical contrast (speckle contrast), a sample-independent beamline parameter')
@describe_input('baseline', 'baseline of one time correlation equal to one for ergodic samples')
@describe_input('correlation_threshold', 'threshold defining which g2 values to fit')
@describe_output('fit_curve', 'Fitted model of the g2 curve')
@describe_output('relaxation_rate', 'Relaxation time associated with the samples dynamics')
@intent(PlotIntent,
        match_key='1-time Correlation',
        name='g2 fit',
        labels={"bottom": "&tau;", "left": "g2"},
        output_map={'x':'tau', 'y':'fit_curve'})
@categories(('Scattering', 'Fitting'))
def fit_scattering_factor(g2: np.ndarray,
                          tau: np.ndarray,
                          beta: float = 1.0,
                          baseline: float = 1.0,
                          correlation_threshold: float = 1.5) -> Tuple[np.ndarray, float]:
    relaxation_rate = 0.01  # Some initial guess
    model = ScatteringModel(beta, baseline, relaxation_rate=relaxation_rate)
    fitting_algorithm = fitting.SLSQPLSQFitter()
    threshold = min(len(tau), np.argmax(g2 < correlation_threshold))

    fit = fitting_algorithm(model, tau[:threshold], g2[:threshold])

    relaxation_rate = fit.relaxation_rate
    fit_curve = fit(tau)

    return fit_curve, relaxation_rate

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
