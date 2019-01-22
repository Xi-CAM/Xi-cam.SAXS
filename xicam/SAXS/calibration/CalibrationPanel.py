from qtpy.QtCore import *
from qtpy.QtWidgets import *
from qtpy.QtGui import *
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
    sigDoCalibrateWorkflow = Signal(object)

    def __init__(self, headermodel: QStandardItemModel, selectionmodel: QItemSelectionModel):
        super(CalibrationPanel, self).__init__()

        self.selectionmodel = selectionmodel
        self.headermodel = headermodel

        self.header().close()

        calibrants = dict(zip(calibrant.ALL_CALIBRANTS.keys(), calibrant.ALL_CALIBRANTS.values()))
        self.device = pTypes.ListParameter(name='Device', type='list', values=[], value='')
        self.calibrant = pTypes.ListParameter(name='Calibrant Material', values=calibrants, value=calibrants['AgBh'])
        self.autoCalibrateMethod = pTypes.ListParameter(name='Algorithm', values=self.algorithms.keys())
        self.autoCalibrateAction = pTypes.ActionParameter(name='Auto Calibrate')
        self.autoCalibrateAction.sigActivated.connect(self.calibrate)
        self.calibratetext = pTypes.TextParameter(name='Instructions', value='', readonly=True, visible=False)

        self.parameter = pTypes.GroupParameter(name='Calibration', children=[self.device,
                                                                             self.calibrant,
                                                                             self.autoCalibrateMethod,
                                                                             self.autoCalibrateAction,
                                                                             self.autoCalibrateAction,
                                                                             self.calibratetext
                                                                             ])

        self.setParameters(self.parameter, showTop=False)

        self.workflow = FourierCalibrationWorkflow()

    def calibrate(self):
        self.sigDoCalibrateWorkflow.emit(self.workflow)

    def dataChanged(self, start, end, _):
        if not self.headermodel.itemFromIndex(self.selectionmodel.currentIndex()): return
        devices = self.headermodel.itemFromIndex(self.selectionmodel.currentIndex()).header.devices()
        self.parameter.param('Device').setLimits(list(set(devices)))
        self.parameter.param('Device').setValue(list(devices)[0])