from xicam.core.execution.workflow import Workflow
from .fourierautocorrelation import fourierAutocorrelation
from xicam.SAXS.processing.arrayrotate import ArrayRotate
from xicam.SAXS.processing.arraytranspose import ArrayTranspose
from xicam.SAXS.calibration.simulatecalibrant import SimulateCalibrant
from .naivesdd import NaiveSDD


class FourierCalibrationWorkflow(Workflow):
    def __init__(self):
        super(FourierCalibrationWorkflow, self).__init__('Fourier Calibration')

        rotate = ArrayRotate()
        rotate.k.value = 3

        transpose = ArrayTranspose()

        autocor = fourierAutocorrelation()

        sdd = NaiveSDD()

        self.processes = [rotate, transpose, autocor, sdd]
        self.autoConnectAll()

    # def execute(self, connection, data=None, ai=None, calibrant=None, **kwargs):
    #     self.processes[0].data.value = data
    #     self.processes[2].ai.value = ai
    #     self.processes[3].calibrant.value = calibrant
    #     return super(FourierCalibrationWorkflow, self).execute(connection,**kwargs)


class SimulateWorkflow(Workflow):
    def __init__(self):
        super(SimulateWorkflow, self).__init__('Calibrant Simulation')

        simulate = SimulateCalibrant()

        self.processes = [simulate]
