from xicam.core.execution.workflow import Workflow
from .fourierautocorrelation import fourier_autocorrelation
from xicam.SAXS.calibration.simulatecalibrant import simulate_calibrant
from .naivesdd import naive_sdd


class FourierCalibrationWorkflow(Workflow):
    def __init__(self):
        super(FourierCalibrationWorkflow, self).__init__('Fourier Calibration')

        autocor = fourier_autocorrelation()

        sdd = naive_sdd()

        self.add_operations(autocor, sdd)
        self.auto_connect_all()


class SimulateWorkflow(Workflow):
    def __init__(self):
        super(SimulateWorkflow, self).__init__('Calibrant Simulation')

        simulate = simulate_calibrant()

        self.add_operations(simulate)
