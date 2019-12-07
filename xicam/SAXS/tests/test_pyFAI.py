# from xicam.SAXS.patches.pyFAI import *
import dill
import pyFAI
# from distributed.protocol.serialize import serialize as dumps, deserialize as loads
from pickle import dumps, loads

def test_Detector_pickle():
    import cloudpickle
    import numpy as np
    from pyFAI.detectors import Pilatus2M
    det = Pilatus2M()

    print(det, type(det))

    # print(det.__reduce__())
    # print(det.__getnewargs_ex__())
    # print(det.__getstate__())

    assert dumps(det)
    assert loads(dumps(det))
    assert loads(dumps(det)).shape == (1679, 1475)


def test_AzimuthalIntegrator_pickle():
    import dill
    import numpy as np
    from pyFAI.azimuthalIntegrator import AzimuthalIntegrator

    det = pyFAI.detectors.detector_factory('pilatus2m')
    ai = AzimuthalIntegrator(detector=det)
    ai.set_wavelength(.1)
    spectra = ai.integrate1d(np.ones(det.shape), 1000)  # force lut generation
    dump = dumps(ai)
    newai = loads(dump)
    assert np.array_equal(newai.integrate1d(np.ones(det.shape), 1000), spectra)
    assert newai.detector.shape == (1679, 1475)


def test_Calibrant():
    from pyFAI import calibrant
    calibrant = calibrant.CalibrantFactory()('AgBh')
    assert dumps(calibrant)
    assert loads(dumps(calibrant))
