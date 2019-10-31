import numpy as np
import skbeam.core.correlation as corr
from astropy.modeling import Fittable1DModel, Parameter, fitting

from xicam.plugins.hints import PlotHint
from xicam.plugins.processingplugin import Input, InputOutput, Output, ProcessingPlugin

class ScatteringModel(Fittable1DModel):
    inputs = ('lag_steps',)
    outputs = ('g2',)

    relaxation_rate = Parameter()

    def __init__(self, beta, baseline=1.0, **kwargs):
        self.beta = beta
        self.baseline = baseline
        super(ScatteringModel, self).__init__(**kwargs)

    def evaluate(self, lag_steps, relaxation_rate):
        return corr.auto_corr_scat_factor(lag_steps, self.beta, relaxation_rate, self.baseline)

    def fit_deriv(self, lag_steps, relaxation_rate):
        d_relaxation_rate = -2 * self.beta * relaxation_rate * np.exp(-2 * relaxation_rate * lag_steps)
        return [d_relaxation_rate]


class FitScatteringFactor(ProcessingPlugin):
    name = "Fit Scattering Factor"

    g2 = InputOutput(name='norm-0-g2',
                     description="normalized intensity-intensity time autocorrelation",
                     type=np.ndarray,
                     visible=False)
    lag_steps = InputOutput(name='tau',
                            description="delay time",
                            type=np.ndarray,
                            visible=False)

    beta = Input(description="optical contrast (speckle contrast), a sample-independent beamline parameter",
                 type=float,
                 name="speckle contrast",
                 default=1.0)
    baseline = Input(description="baseline of one time correlation equal to one for ergodic samples",
                     type=float,
                     default=1.0)
    correlation_threshold = Input("threshold defining which g2 values to fit",
                                  type=float,
                                  default=1.5)

    fit_curve = Output(description="fitted model of the g2 curve",
                       type=np.ndarray)
    relaxation_rate = Output(description="relaxation time associated with the samples dynamics",
                             type=float)

    def evaluate(self):
        relaxation_rate = 0.01  # Some initial guess
        model = ScatteringModel(self.beta.value, self.baseline.value, relaxation_rate=relaxation_rate)
        fitter = fitting.SLSQPLSQFitter()
        threshold = min(len(self.lag_steps.value), np.argmax(self.g2.value < self.correlation_threshold.value))

        fit = fitter(model, self.lag_steps.value[:threshold], self.g2.value[:threshold])

        self.relaxation_rate.value = fit.relaxation_rate.value
        self.fit_curve.value = fit(self.lag_steps.value)

        self.hints = [PlotHint(self.lag_steps, self.fit_curve, name="1-Time Fit")]
