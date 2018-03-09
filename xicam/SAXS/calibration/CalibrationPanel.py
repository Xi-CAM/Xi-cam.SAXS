from qtpy.QtCore import *
from qtpy.QtWidgets import *
import pyqtgraph.parametertree.parameterTypes as pTypes
from pyqtgraph.parametertree import Parameter, ParameterTree, ParameterItem, registerParameterType
from pyFAI import calibrant
from collections import OrderedDict
from .workflows import FourierCalibrationWorkflow


class CalibrationPanel(ParameterTree):
    algorithms = OrderedDict(
        [('Fourier Autocorrelation', None),
         ('2D Ricker Wavelet', None),
         ('DPDAK Refinement', None)])
    sigCalibrate = Signal(object, str)
    sigSimulateCalibrant = Signal(str)
    sigDoCalibrateWorkflow = Signal(object)

    def __init__(self):
        super(CalibrationPanel, self).__init__()

        self.header().close()

        self.autoCalibrateAction = pTypes.ActionParameter(name='Auto Calibrate')
        self.autoCalibrateAction.sigActivated.connect(self.calibrate)

        calibrants = sorted(calibrant.ALL_CALIBRANTS.all.keys())
        self.calibrant = pTypes.ListParameter(name='Calibrant Material', values=calibrants)

        self.autoCalibrateMethod = pTypes.ListParameter(name='Algorithm', values=self.algorithms.keys())

        # self.overlayAction = pTypes.ActionParameter(name='Simulate Calibrant')
        # self.overlayAction.sigActivated.connect(self.simulatecalibrant)

        self.setParameters(pTypes.GroupParameter(name='Calibration', children=[self.calibrant,
                                                                               self.autoCalibrateMethod,
                                                                               self.autoCalibrateAction, ]),
                           showTop=False)

        self.workflow = FourierCalibrationWorkflow()

    def calibrate(self):
        self.sigDoCalibrateWorkflow.emit(self.workflow)

    def simulatecalibrant(self):
        self.sigSimulateCalibrant.emit(self.calibrant.value())
