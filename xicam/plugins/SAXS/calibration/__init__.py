from collections import OrderedDict

import qdarkstyle
from qtmodern import styles
from qtpy.QtGui import *
from qtpy.QtWidgets import QApplication
from xicam.gui.static import path
import pyqtgraph as pg
from pyFAI import detectors, AzimuthalIntegrator

from xicam.plugins import SettingsPlugin
from .CalibrationPanel import CalibrationPanel

CalibrationSettings = SettingsPlugin.fromParameter(QIcon(str(path('icons/calibrate.png'))),
                                                   'CalibrationSettings',
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
                                                     'suffix': u'°'}])


def apply(self):
    AI = AzimuthalIntegrator(
        wavelength=CalibrationSettings.parameter['Wavelength'])
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


CalibrationSettings.apply = apply
