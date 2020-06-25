from collections import namedtuple

import fabio
import numpy as np
from pyFAI import detectors, calibrant
from pyFAI.azimuthalIntegrator import AzimuthalIntegrator
import pytest

from xicam.core import execution
from xicam.core.execution import localexecutor
from xicam.SAXS.calibration.workflows import FourierCalibrationWorkflow
from xicam.SAXS.workflows.xpcs import OneTime, TwoTime


execution.executor = localexecutor.LocalExecutor()


def test_FourierCalibrationWorkflow():
    workflow = FourierCalibrationWorkflow()

    data = fabio.open('/home/rp/data/YL1031/AGB_5S_USE_2_2m.edf').data
    ai = AzimuthalIntegrator()
    ai.set_wavelength(124e-12)
    ai.detector = detectors.Pilatus2M()
    c = calibrant.ALL_CALIBRANTS('AgBh')

    print(workflow.execute(None, data=data, ai=ai, calibrant=c, callback_slot=print))


FRAMES = 100
SHAPE = (10, 10)

@pytest.fixture
def images():
    return np.random.random((FRAMES, *SHAPE))

@pytest.fixture
def labels():
    return np.ones(SHAPE)


class TestOneTimeWorkflow:
    def test_no_darks(self, images, labels):
        workflow = TwoTime()
        workflow.execute_synchronous(images=images, labels=labels)
        # TODO should dark correction be required?

    def test_with_darks(self):
        workflow = TwoTime()
        workflow.execute_synchronous(images=images,
                                     labels=labels,
                                     darks=None,
                                     flats=None)


class TestTwoTimeWorkflow:
    def test_no_darks(self, images, labels):
        workflow = TwoTime()
        result = workflow.execute_synchronous(images=images,
                                              labels=labels)
        print(result)

    def test_with_darks(self):
        ...