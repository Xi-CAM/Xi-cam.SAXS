from xicam.plugins import ProcessingPlugin, Input, Output
import numpy as np
from pyFAI import AzimuthalIntegrator, units


class QIntegratePlugin(ProcessingPlugin):
    integrator = Input(description='A PyFAI.AzimuthalIntegrator object',
                       type=AzimuthalIntegrator)
    data = Input(description='2d array representing intensity for each pixel',
                 type=np.ndarray)
    npt = Input(description='Number of bins along q')
    polz_factor = Input(description='Polarization factor for correction',
                        type=float)
    unit = Input(description='Output units for q',
                 type=[str, units.Unit],
                 default="q_A^-1")
    radial_range = Input(description='The lower and upper range of the radial unit. If not provided, range is simply '
                                     '(data.min(), data.max()). Values outside the range are ignored.',
                         type=tuple)
    azimuth_range = Input(description='The lower and upper range of the azimuthal angle in degree. If not provided, '
                                      'range is simply (data.min(), data.max()). Values outside the range are ignored.')
    mask = Input(description='Array (same size as image) with 1 for masked pixels, and 0 for valid pixels',
                 type=np.ndarray)
    dark = Input(description='Dark noise image',
                 type=np.ndarray)
    flat = Input(description='Flat field image',
                 type=np.ndarray)
    method = Input(description='Can be "numpy", "cython", "BBox" or "splitpixel", "lut", "csr", "nosplit_csr", '
                               '"full_csr", "lut_ocl" and "csr_ocl" if you want to go on GPU. To Specify the device: '
                               '"csr_ocl_1,2"',
                   type=str)
    normalization_factor = Input(description='Value of a normalization monitor',
                                 type=float)
    q = Output(description='Q bin center positions',
               type=np.array)
    iq4 = Output(description='Binned/pixel-split integrated intensity',
               type=np.array)

    def evaluate(self):
        self.q.value, self.I.value = self.integrator.value.integrate1d(data=self.data.value,
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
        self.iq4.value = self.I.value * (self.q.value ** 4)

