from xicam.plugins import ProcessingPlugin, Input, Output
import numpy as np
from pyFAI import AzimuthalIntegrator, units


class ZIntegratePlugin(ProcessingPlugin):
    name = 'Z Integrate'
    ai = Input(description='A PyFAI.AzimuthalIntegrator object',
               type=AzimuthalIntegrator)
    data = Input(description='2d array representing intensity for each pixel',
                 type=np.ndarray)
    mask = Input(description='Array (same size as image) with 1 for masked pixels, and 0 for valid pixels',
                 type=np.ndarray)
    dark = Input(description='Dark noise image',
                 type=np.ndarray)
    flat = Input(description='Flat field image',
                 type=np.ndarray)

    normalization_factor = Input(description='Value of a normalization monitor',
                                 type=float, default=1.)
    qz = Output(description='Q_x bin center positions',
                type=np.array)
    I = Output(description='Binned/pixel-split integrated intensity',
               type=np.array)

    def evaluate(self):
        if self.dark.value is None: self.dark.value = np.zeros_like(self.data.value)
        if self.flat.value is None: self.flat.value = np.ones_like(self.data.value)
        if self.mask.value is None: self.mask.value = np.zeros_like(self.data.value)
        self.I.value = np.sum((self.data.value - self.dark.value) * np.average(self.flat.value - self.dark.value) / (
                    self.flat.value - self.dark.value), axis=1)[::-1]
        centerx = self.ai.value.getFit2D()['centerX']
        centerz = self.ai.value.getFit2D()['centerY']
        self.qz.value = self.ai.value.qFunction(np.arange(0, self.data.value.shape[0]),
                                                np.array([centerx] * self.data.value.shape[0])) / 10
        self.qz.value[np.arange(0, self.data.value.shape[0]) < centerz] *= -1.
