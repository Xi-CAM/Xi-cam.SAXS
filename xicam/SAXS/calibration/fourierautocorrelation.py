import numpy as np
from scipy import signal
from xicam.plugins import ProcessingPlugin, Input, Output, InOut
from pyFAI import AzimuthalIntegrator

class fourierAutocorrelation(ProcessingPlugin):
    name = 'Fourier Autocorrelation'

    data = Input(description='Calibrant frame image data',
                 type=np.ndarray)
    center = Output(description='Approximated position of the direct beam center')
    ai = InOut(description='Azimuthal integrator; center will be modified in place', type=AzimuthalIntegrator)

    def evaluate(self):
        mask = self.ai.value.detector.mask
        data = np.array(self.data.value)
        if isinstance(mask, np.ndarray) and mask.shape == self.data.value.shape:
            data = data * (1 - mask)

        con = signal.fftconvolve(data, data) / np.sqrt(
            signal.fftconvolve(np.ones_like(self.data.value), np.ones_like(self.data.value)))

        self.center.value = np.array(np.unravel_index(con.argmax(), con.shape)) / 2.
        fit2dparams = self.ai.value.getFit2D()
        fit2dparams['centerX'] = self.center.value[1]
        fit2dparams['centerY'] = self.center.value[0]
        self.ai.value.setFit2D(**fit2dparams)
