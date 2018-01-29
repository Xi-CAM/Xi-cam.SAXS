from collections import OrderedDict

import qdarkstyle
from qtmodern import styles
from qtpy.QtGui import *
from qtpy.QtWidgets import QApplication
from qtpy.QtCore import Signal
from xicam.gui.static import path
import pyqtgraph as pg
from pyFAI import detectors, AzimuthalIntegrator

from xicam.plugins import SettingsPlugin
from .CalibrationPanel import CalibrationPanel

from pyqtgraph.parametertree import Parameter, ParameterTree


# https://stackoverflow.com/questions/20866996/how-to-compress-slot-calls-when-using-queued-connection-in-qt

class DeviceProfiles(SettingsPlugin):
    sigRequestRedraw = Signal()
    sigRequestReduce = Signal()

    name = 'Device Profiles'

    def __init__(self):
        children = [{'name': 'Device', 'type': 'list', 'children':
            [{'name': 'Geometry Style', 'type': 'list',
              'values': ['Fit2D', 'pyFAI', 'wxDiff']},
             {'name': 'Detector', 'type': 'list',
              'values': detectors.ALL_DETECTORS},
             {'name': 'Pixel Size X', 'type': 'float', 'value': 172.e-6,
              'siPrefix': True, 'suffix': 'm',
              'step': 1e-6},
             {'name': 'Pixel Size Y', 'type': 'float', 'value': 172.e-6,
              'siPrefix': True, 'suffix': 'm',
              'step': 1e-6},
             {'name': 'Center X', 'type': 'float', 'value': 0, 'suffix': ' px'},
             {'name': 'Center Y', 'type': 'float', 'value': 0, 'suffix': ' px'},
             {'name': 'Detector Distance', 'type': 'float', 'value': 1,
              'siPrefix': True, 'suffix': 'm',
              'step': 1e-3},
             {'name': 'Detector Tilt', 'type': 'float', 'value': 0,
              'siPrefix': False, 'suffix': u'°',
              'step': 1e-1},
             {'name': 'Detector Rotation', 'type': 'float', 'value': 0,
              'siPrefix': False, 'suffix': u'°',
              'step': 1e-1},
             {'name': 'Energy', 'type': 'float', 'value': 10000,
              'siPrefix': True,
              'suffix': 'eV'},
             {'name': 'Wavelength', 'type': 'float', 'value': 1,
              'siPrefix': True,
              'suffix': 'm'},
             # {'name': 'View Mask', 'type': 'action'},
             {'name': 'Incidence Angle (GIXS)', 'type': 'float', 'value': 0.1,
              'suffix': u'°'}]
                     }]

        widget = ParameterTree()
        self.parameter = Parameter(name="Device Profiles", type='group', children=children)
        widget.setParameters(self.parameter, showTop=False)
        icon = QIcon(str(path('icons/calibrate.png')))
        super(DeviceProfiles, self).__init__(icon, "Device Profiles", widget)

        self.parameter.sigValueChanged.connect(self.sigRequestRedraw)
        self.parameter.sigValueChanged.connect(self.sigRequestReduce)

    def setModel(self, headermodel):
        self.headermodel = headermodel
        self.headermodel.dataChanged.connect(self.dataChanged)

    def dataChanged(self, start, end):
        previousdevice = self.parameter['Device']
        devices = self.headermodel.item(0).header.devices()
        self.parameter.param('Device').setLimits(devices)
        if previousdevice in devices: self.parameter.param('Device').setValue(previousdevice)

    def apply(self):
        AI = AzimuthalIntegrator(
            wavelength=self.parameter.child('Device')['Wavelength'])
        # if Calibration.isChecked():
        #     AI.setFit2D(self.getvalue('Detector Distance') * 1000.,
        #                 self.getvalue('Center X'),
        #                 self.getvalue('Center Y'),
        #                 self.getvalue('Detector Tilt'),
        #                 360. - self.getvalue('Detector Rotation'),
        #                 self.getvalue('Pixel Size Y') * 1.e6,
        #                 self.getvalue('Pixel Size X') * 1.e6)
        # elif self.wxdiffstyle.isChecked():
        #     AI.setFit2D(self.getvalue('Detector Distance') * 1000.,
        #                 self.getvalue('Center X'),
        #                 self.getvalue('Center Y'),
        #                 self.getvalue('Detector Tilt') / 2. / np.pi * 360.,
        #                 360. - (2 * np.pi - self.getvalue('Detector Rotation')) / 2. / np.pi * 360.,
        #                 self.getvalue('Pixel Size Y') * 1.e6,
        #                 self.getvalue('Pixel Size X') * 1.e6)
        # AI.set_wavelength(self.getvalue('Wavelength'))
        # # print AI

        activeCalibration = AI

    def save(self):
        self.apply()
        return self.parameter.saveState(filter='user')

    def restore(self, state):
        self.parameter.restoreState(state, addChildren=False, removeChildren=False)
