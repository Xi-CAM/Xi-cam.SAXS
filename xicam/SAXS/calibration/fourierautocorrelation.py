import numpy as np
from scipy import signal
from xicam.plugins import ProcessingPlugin, Input, Output


class fourierAutocorrelation(ProcessingPlugin):
    name = 'Fourier Autocorrelation'

    data = Input(description='Calibrant frame image data',
                 type=np.ndarray)
    mask = Input(description='Array (same size as image) with 1 for masked pixels, and 0 for valid pixels',
                 type=np.ndarray)
    center = Output(description='Approximated position of the direct beam center')

    def evaluate(self):
        con = signal.fftconvolve(self.data.value * self.mask.value, self.data.value * self.mask.value) / np.sqrt(
            signal.fftconvolve(np.ones_like(self.data.value), np.ones_like(self.data.value)))

        self.center.value = np.array(np.unravel_index(con.argmax(), con.shape)) / 2.
