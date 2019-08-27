from astropy.modeling.models import Gaussian1D
from xicam.plugins.fittablemodelplugin import Fittable1DModelPlugin


class Gaussian1D(Gaussian1D, Fittable1DModelPlugin):
    pass
