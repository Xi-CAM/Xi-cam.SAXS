from xicam.plugins import ProcessingPlugin, Input, Output, PlotHint
import numpy as np
from pyFAI import units
from pyFAI.azimuthalIntegrator import AzimuthalIntegrator


class QIntegratePlugin(ProcessingPlugin):
    ai = Input(description='A PyFAI.AzimuthalIntegrator object',
               type=AzimuthalIntegrator)
    data = Input(description='2d array representing intensity for each pixel',
                 type=np.ndarray)
    npt = Input(description='Number of bins along q', default=1000, type=int)
    polz_factor = Input(description='Polarization factor for correction',
                        type=float, default=0)
    unit = Input(description='Output units for q',
                 type=[str, units.Unit],
                 default="q_A^-1")
    radial_range = Input(description='The lower and upper range of the radial unit. If not provided, range is simply '
                                     '(data.min(), data.max()). Values outside the range are ignored.',
                         type=tuple)
    azimuth_range = Input(description='The lower and upper range of the azimuthal angle in degree. If not provided, '
                                      'range is simply (data.min(), data.max()). Values outside the range are ignored.',
                          type=tuple)
    mask = Input(description='Array (same size as image) with 1 for masked pixels, and 0 for valid pixels',
                 type=np.ndarray)
    dark = Input(description='Dark noise image',
                 type=np.ndarray)
    flat = Input(description='Flat field image',
                 type=np.ndarray)
    method = Input(description='Can be "numpy", "cython", "BBox" or "splitpixel", "lut", "csr", "nosplit_csr", '
                               '"full_csr", "lut_ocl" and "csr_ocl" if you want to go on GPU. To Specify the device: '
                               '"csr_ocl_1,2"',
                   type=str, default='splitbbox')
    normalization_factor = Input(description='Value of a normalization monitor',
                                 type=float, default=1.)
    q = Output(description='Q bin center positions',
               type=np.array)
    Iq = Output(description='Binned/pixel-split integrated intensity',
                type=np.array)

    # hints = [PlotHint(q, Iq)]

    def evaluate(self):
        self.q.value, self.Iq.value = self.ai.value.integrate1d(data=self.data.value,
                                                                npt=self.npt.value,
                                                                radial_range=self.radial_range.value,
                                                                azimuth_range=self.azimuth_range.value,
                                                                mask=self.mask.value,
                                                                polarization_factor=self.polz_factor.value,
                                                                dark=self.dark.value,
                                                                flat=self.flat.value,
                                                                method=self.method.value,
                                                                unit=self.unit.value,
                                                                normalization_factor=self.normalization_factor.value)

        self.hints = [PlotHint(self.q.value, self.Iq.value, name="Q Integrate")]
