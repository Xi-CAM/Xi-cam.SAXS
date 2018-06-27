from astropy.modeling.models import Gaussian1D, Shift
from xicam.plugins.FittableModelPlugin import Fittable1DModelPlugin

ShiftedGaussian1D = Gaussian1D + Shift


class ShiftedGaussian1D(ShiftedGaussian1D, Fittable1DModelPlugin):
    pass
