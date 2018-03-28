from xicam.SAXS.calibration.workflows import FourierCalibrationWorkflow
import fabio
from pyFAI import AzimuthalIntegrator, detectors, calibrant


def test_FourierCalibrationWorkflow():
    workflow = FourierCalibrationWorkflow()

    data = fabio.open('/home/rp/data/YL1031/AGB_5S_USE_2_2m.edf').data
    ai = AzimuthalIntegrator()
    ai.set_wavelength(124e-12)
    ai.detector = detectors.Pilatus2M()
    c = calibrant.ALL_CALIBRANTS('AgBh')

    print(workflow.execute(None, data=data, ai=ai, calibrant=c, callback_slot=print))
