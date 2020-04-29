from xicam.plugins.operationplugin import operation, output_names, display_name, describe_input, describe_output, \
     categories, plot_hint
import numpy as np
from typing import Tuple
from pyFAI import units
from pyFAI.azimuthalIntegrator import AzimuthalIntegrator




@operation
@display_name('q Integration')
@output_names('q', 'I')
@describe_input('integrator', 'A PyFAI.AzimuthalIntegrator object')
@describe_input('data', '2d array representing intensity for each pixel')
@describe_input('npt', 'Number of bins along q')
@describe_input('polz_factor', 'Polarization factor for correction')
@describe_input('unit', 'Output units for q')
@describe_input('radial_range', 'The lower and upper range of the radial unit. If not provided, range is simply '
                                '(data.min(), data.max()). Values outside the range are ignored.')
@describe_input('azimuth_range', 'The lower and upper range of the azimuthal angle in degree. If not provided, '
                                 'range is simply (data.min(), data.max()). Values outside the range are ignored.')
@describe_input('mask', 'Array (same size as image) with 1 for masked pixels, and 0 for valid pixels')
@describe_input('dark', 'Dark noise image')
@describe_input('flat', 'Flat field image')
@describe_input('method', 'Can be "numpy", "cython", "BBox" or "splitpixel", "lut", "csr", "nosplit_csr", '
                          '"full_csr", "lut_ocl" and "csr_ocl" if you want to go on GPU. To Specify the device: '
                          '"csr_ocl_1,2"')
@describe_input('normalization_factor', 'Value of a normalization monitor')
@describe_output('q2', 'Q squared bin center positions')
@describe_output('ln_I', 'Logarithm of Binned/pixel-split integrated intensity')
@plot_hint("qˆ2", "ln_I", name="Guinier plot")
@categories(("Scattering", "Integration"))

def guinier_plot(integrator: AzimuthalIntegrator,
                data: np.ndarray,
                npt: int = 1000,
                polz_factor: float = 0,
                unit: Union[str, units.Unit] = "q_A^-1",
                radial_range: Tuple[float, float] = None,
                azimuth_range: Tuple[float, float] = None,
                mask: np.ndarray = None,
                dark: np.ndarray = None,
                flat: np.ndarray = None,
                method: str = 'splitbbox',
                normalization_factor: float = 1, ) -> Tuple[np.ndarray, np.ndarray]:
    q, I = integrator.integrate1d(data=data,
                                  npt=npt,
                                  radial_range=radial_range,
                                  azimuth_range=azimuth_range,
                                  mask=mask,
                                  polarization_factor=polz_factor,
                                  dark=dark,
                                  flat=flat,
                                  method=method,
                                  unit=unit,
                                  normalization_factor=normalization_factor)
    q2 = q**2
    ln_I = np.log(I)
    return q2, ln_I

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

    q2 = Output(description='Q bin center positions',
               type=np.array)
    ln_I = Output(description='Binned/pixel-split integrated intensity',
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
        self.q2.value = self.q.value ** 2
        self.ln_I.value = np.log(self.I.value)

