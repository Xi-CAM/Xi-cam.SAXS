from astropy.modeling.models import Gaussian1D, Shift
from xicam.plugins.fittablemodelplugin import Fittable1DModelPlugin


class ShiftedGaussian1D(Fittable1DModelPlugin):
    def __new__(cls, *args, **kwargs):
        return Gaussian1D(*args, **kwargs) + Shift(*args, **kwargs)
