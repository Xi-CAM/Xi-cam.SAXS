from qtpy.QtGui import *
from qtpy.QtCore import Signal
from qtpy.QtWidgets import *
from xicam.gui.static import path
from pyFAI import detectors, AzimuthalIntegrator
from pyFAI.multi_geometry import MultiGeometry

from xicam.plugins import SettingsPlugin
from .CalibrationPanel import CalibrationPanel

from pyqtgraph.parametertree import Parameter, ParameterTree
from pyqtgraph.parametertree.parameterTypes import GroupParameter, ListParameter, SimpleParameter


# https://stackoverflow.com/questions/20866996/how-to-compress-slot-calls-when-using-queued-connection-in-qt

class DeviceParameter(GroupParameter):
    def __init__(self, device, **opts):
        opts['type'] = 'bool'
        opts['value'] = True
        opts['name'] = device
        ALL_DETECTORS = {(getattr(detector, 'aliases', ) or [detector.__name__])[0]: detector for detector in
                         detectors.ALL_DETECTORS.values()}
        geometrystyle = ListParameter(name='Geometry Style', type='list',
                                      values=['Fit2D', 'pyFAI', 'wxDiff'], value='Fit2D')
        detector = ListParameter(name='Detector', type='list', values=ALL_DETECTORS)
        pixelx = SimpleParameter(name='Pixel Size X', type='float', value=172.e-6, siPrefix=True, suffix='m')
        pixely = SimpleParameter(name='Pixel Size Y', type='float', value=172.e-6, siPrefix=True, suffix='m')
        binning = SimpleParameter(name='Binning', type='int', value=1, suffix='x', limits=(1, 100))
        centerx = SimpleParameter(name='Center X', type='float', value=0, suffix=' px', decimals=4)
        centery = SimpleParameter(name='Center Y', type='float', value=0, suffix=' px', decimals=4)
        sdd = SimpleParameter(name='Detector Distance', type='float', value=1, siPrefix=True, suffix='m',
                              limits=(0, 1000))
        tilt = SimpleParameter(name='Detector Tilt', type='float', value=0, siPrefix=False, suffix=u'°')
        rotation = SimpleParameter(name='Detector Rotation', type='float', value=0, siPrefix=False, suffix=u'°')

        self.children = [geometrystyle, detector, pixelx, pixely, binning, centerx, centery, sdd, tilt, rotation]
        opts['children'] = self.children
        super(DeviceParameter, self).__init__(**opts)
        #     wavelengthparam = self.param('Wavelength')
        #     energyparam = self.param('Energy')
        #     wavelengthparam.sigValueChanged.connect(self.wavelengthChanged)
        #     energyparam.sigValueChanged.connect(self.energyChanged)
        #
        #


class DeviceProfiles(SettingsPlugin):
    sigRequestRedraw = Signal()
    sigRequestReduce = Signal()

    name = 'Device Profiles'

    def __init__(self):
        self.multiAI = MultiGeometry([])
        self.AIs = {}

        widget = ParameterTree()
        device = ListParameter(name='Device', type='list', values=[], value='')
        energy = SimpleParameter(name='Energy', type='float', value=10000, siPrefix=True, suffix='eV')
        wavelength = SimpleParameter(name='Wavelength', type='float', value=1.239842e-6 / 10000, siPrefix=True,
                                     suffix='m')
        self.parameter = Parameter(name="Device Profiles", type='group', children=[device, energy, wavelength])
        widget.setParameters(self.parameter, showTop=False)
        icon = QIcon(str(path('icons/calibrate.png')))
        super(DeviceProfiles, self).__init__(icon, "Device Profiles", widget)

        self.parameter.sigValueChanged.connect(self.sigRequestRedraw)
        self.parameter.sigValueChanged.connect(self.sigRequestReduce)
        self.parameter.sigTreeStateChanged.connect(self.genAIs)

    def genAIs(self, parent, changes):
        for parameter, key, value in changes:
            if key == 'value' and self.parameter['Device'] in self.AIs:
                ai = self.AIs[self.parameter['Device']]  # type: AzimuthalIntegrator
                if parameter.name == 'Wavelength':
                    self.parameter.param('Energy').setValue(1.239842e-6 / self.param('Wavelength').value(),
                                                            blockSignal=self.parameter.sigTreeStateChanged)
                    ai.set_wavelength(value)
                elif parameter.name == 'Energy':
                    self.parameter.param('Wavelength').setValue(1.239842e-6 / self.param('Energy').value(),
                                                                blockSignal=self.WavelengthChanged)
                    ai.set_wavelength(self.parameter['Wavelength'])
                elif parameter.name == 'Detector':
                    ai.detector = value
                elif parameter.name == 'Binning':
                    ai.detector.set_binning(value)
                elif parameter.name == 'Pixel Size X':
                    ai.detector.set_pixel1(value)
                elif parameter.name == 'Pixel Size Y':
                    ai.detector.set_pixel2(value)
                elif parameter.name == 'Center X':
                    fit2d = ai.getFit2D()
                    fit2d['centerX'] = value
                    ai.setFit2D(**fit2d)
                elif parameter.name == 'Center Y':
                    fit2d = ai.getFit2D()
                    fit2d['centerY'] = value
                    ai.setFit2D(**fit2d)
                elif parameter.name == 'Detector Distance':
                    fit2d = ai.getFit2D()
                    fit2d['directDist'] = value
                    ai.setFit2D(**fit2d)
                elif parameter.name == 'Detector Tilt':
                    fit2d = ai.getFit2D()
                    fit2d['tilt'] = value
                    ai.setFit2D(**fit2d)
                elif parameter.name == 'Detector Rotation':
                    fit2d = ai.getFit2D()
                    fit2d['tiltPlanRotation'] = value
                    ai.setFit2D(**fit2d)

    def AI(self, device):
        return self.AIs[device]

    def setAI(self, ai: AzimuthalIntegrator, device: str):
        self.AIs[device] = ai
        self.multiAI.ais = self.AIs.values()

        # propagate new ai to parameter
        fit2d = ai.getFit2D()
        self.parameter.child(device, 'Detector').setValue(
            type(ai.detector))  # (getattr(ai.detector,'aliases') or [ai.detector.__class__.__name__])[0]
        self.parameter.child(device, 'Binning').setValue(ai.detector.binning[0])
        self.parameter.child(device, 'Detector Tilt').setValue(fit2d['tiltPlanRotation'])
        self.parameter.child(device, 'Detector Rotation').setValue(fit2d['tilt'])
        self.parameter.child(device, 'Pixel Size X').setValue(ai.pixel1)
        self.parameter.child(device, 'Pixel Size Y').setValue(ai.pixel2)
        self.parameter.child(device, 'Center X').setValue(fit2d['centerX'])
        self.parameter.child(device, 'Center Y').setValue(fit2d['centerY'])
        self.parameter.child(device, 'Detector Distance').setValue(fit2d['directDist'])
        self.parameter.child('Wavelength').setValue(ai.wavelength)

    def addDevice(self, device):
        devicechild = DeviceParameter(device)
        self.parameter.addChild(devicechild)
        ai = AzimuthalIntegrator(wavelength=self.parameter['Wavelength'])
        self.AIs[device] = ai
        self.multiAI.ais = list(self.AIs.values())

    def setModel(self, headermodel):
        self.headermodel = headermodel
        self.headermodel.dataChanged.connect(self.dataChanged)

    def dataChanged(self, start, end):
        previousdevice = self.parameter['Device']
        devices = self.headermodel.item(0).header.devices()
        deviceparam = self.parameter.param('Device')
        deviceparam.setLimits(list(set(deviceparam.opts['limits']) | devices))
        if previousdevice in devices:
            self.parameter.param('Device').setValue(previousdevice)
        else:
            for device in list(devices):
                self.addDevice(device)
            self.parameter.param('Device').setValue(list(devices)[0])

    def apply(self):
        AI = AzimuthalIntegrator(
            wavelength=self.parameter.child('Wavelength').value())
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
        pass
        # self.parameter.restoreState(state, addChildren=False, removeChildren=False)

    def wavelengthChanged(self):
        self.param('Energy').setValue(1.239842e-6 / self.param('Wavelength').value(), blockSignal=self.EnergyChanged)

    def energyChanged(self):
        self.param('Wavelength').setValue(1.239842e-6 / self.param('Energy').value(),
                                          blockSignal=self.WavelengthChanged)
