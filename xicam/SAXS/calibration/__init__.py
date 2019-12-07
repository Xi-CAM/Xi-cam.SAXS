from qtpy.QtGui import *
from qtpy.QtCore import Signal, Qt
from qtpy.QtWidgets import *
from xicam.gui.static import path
from pyFAI import detectors
from pyFAI.azimuthalIntegrator import AzimuthalIntegrator
from pyFAI.multi_geometry import MultiGeometry

from xicam.plugins import ParameterSettingsPlugin
from xicam.core import msg
from .CalibrationPanel import CalibrationPanel

from pyqtgraph.parametertree import Parameter, ParameterTree
from pyqtgraph.parametertree.parameterTypes import GroupParameter, ListParameter, SimpleParameter
from xicam.SAXS.detectors import FastCCD


# https://stackoverflow.com/questions/20866996/how-to-compress-slot-calls-when-using-queued-connection-in-qt

# TODO: Refactor this class to be a view on the AI
class DeviceParameter(GroupParameter):
    def __init__(self, device, **opts):
        opts['type'] = 'bool'
        opts['value'] = True
        opts['name'] = device
        opts['removable'] = True
        ALL_DETECTORS = {(getattr(detector, 'aliases', ) or [detector.__name__])[0]: detector for detector in
                         detectors.ALL_DETECTORS.values()}
        geometrystyle = ListParameter(name='Geometry Style', type='list',
                                      values=['Fit2D', 'pyFAI', 'wxDiff'], value='Fit2D')
        detector = ListParameter(name='Detector', type='list', values=ALL_DETECTORS, value=ALL_DETECTORS['Fast CCD'])
        pixelx = SimpleParameter(name='Pixel Size X', type='float', value=172.e-6, siPrefix=True, suffix='m')
        pixely = SimpleParameter(name='Pixel Size Y', type='float', value=172.e-6, siPrefix=True, suffix='m')
        binning = SimpleParameter(name='Binning', type='int', value=1, suffix='x', limits=(1, 100))
        centerx = SimpleParameter(name='Center X', type='float', value=0, suffix=' px', decimals=4)
        centery = SimpleParameter(name='Center Y', type='float', value=0, suffix=' px', decimals=4)
        sdd = SimpleParameter(name='Detector Distance', type='float', value=1, siPrefix=True, suffix='m',
                              limits=(0, 1000), step=1e-3)
        tilt = SimpleParameter(name='Detector Tilt', type='float', value=0, siPrefix=False, suffix=u'°')
        rotation = SimpleParameter(name='Detector Rotation', type='float', value=0, siPrefix=False, suffix=u'°')

        self.children = [geometrystyle, detector, pixelx, pixely, binning, centerx, centery, sdd, tilt, rotation]
        opts['children'] = self.children
        super(DeviceParameter, self).__init__(**opts)


class DeviceProfiles(ParameterSettingsPlugin):
    sigGeometryChanged = Signal(AzimuthalIntegrator)  # Emits the new geometry

    def __init__(self):
        self.headermodel = None
        self.selectionmodel = None
        self.multiAI = MultiGeometry([])
        self.AIs = dict()
        self._changes = []
        self.isSilent = False


        energy = SimpleParameter(name='Energy', type='float', value=10000, siPrefix=True, suffix='eV')
        wavelength = SimpleParameter(name='Wavelength', type='float', value=1.239842e-6 / 10000, siPrefix=True,
                                     suffix='m')

        icon = QIcon(str(path('icons/calibrate.png')))
        super(DeviceProfiles, self).__init__(icon, "Device Profiles", [energy, wavelength], addText='New Device')

        self.sigTreeStateChanged.connect(self.stateChanged)

    def normalize(self, changes):
        for parameter, key, value in changes:
            if parameter.name == 'Wavelength':
                self.param('Energy').setValue(1.239842e-6 / self.param('Wavelength').value(),
                                              blockSignal=self.parameter.sigTreeStateChanged)
            elif parameter.name == 'Energy':
                self.param('Wavelength').setValue(1.239842e-6 / self.param('Energy').value(),
                                                  blockSignal=self.WavelengthChanged)

    def stateChanged(self, parent, changes):
        self.normalize(changes)

        self._changes.extend(changes)
        if not self.isSilent:
            self.emitChanges()
            self.apply()
            self.save()

    def emitChanges(self):
        modified_AIs = {self.AI(change[0].parent().name()) for change in self._changes if change[0].parent()}
        self._changes = []

        self.genAIs()
        for ai in modified_AIs:
            self.sigGeometryChanged.emit(ai)

    def setSilence(self, silence):
        self.isSilent = silence

        if not silence:
            self.emitChanges()
            self.apply()
            self.save()

    def addNew(self, typ=None):
        text, ok = QInputDialog().getText(self.widget, 'Enter Device Name', 'Device Name:')

        if text and ok:
            self.addDevice(text)

    def genAIs(self):

        for parameter in self.children():
            if isinstance(parameter, DeviceParameter):
                device = parameter.name()
                ai = self.AI(device)
                ai.set_wavelength(self['Wavelength'])
                ai.detector = parameter['Detector']()
                ai.detector.set_binning([parameter['Binning']] * 2)
                ai.detector.set_pixel1(parameter['Pixel Size X'])
                ai.detector.set_pixel2(parameter['Pixel Size Y'])
                fit2d = ai.getFit2D()
                fit2d['centerX'] = parameter['Center X']
                fit2d['centerY'] = ai.detector.shape[0] - parameter['Center Y']
                fit2d['directDist'] = parameter['Detector Distance'] * 1000
                fit2d['tilt'] = parameter['Detector Tilt']
                fit2d['tiltPlanRotation'] = parameter['Detector Rotation']
                ai.setFit2D(**fit2d)

    def AI(self, device):
        if device not in self.AIs:
            self.addDevice(device)
        return self.AIs.get(device, None)

    def setAI(self, ai: AzimuthalIntegrator, device: str):
        self.AIs[device] = ai
        self.multiAI.ais = self.AIs.values()

        # propagate new ai to parameter
        fit2d = ai.getFit2D()
        try:
            self.setSilence(True)
            self.child(device, 'Detector').setValue(type(ai.detector))
            self.child(device, 'Binning').setValue(ai.detector.binning[0])
            self.child(device, 'Detector Tilt').setValue(fit2d['tiltPlanRotation'])
            self.child(device, 'Detector Rotation').setValue(fit2d['tilt'])
            self.child(device, 'Pixel Size X').setValue(ai.pixel1)
            self.child(device, 'Pixel Size Y').setValue(ai.pixel2)
            self.child(device, 'Center X').setValue(fit2d['centerX'])
            self.child(device, 'Center Y').setValue(ai.detector.shape[0] - fit2d['centerY'])
            self.child(device, 'Detector Distance').setValue(fit2d['directDist'] / 1000.)
            self.child('Wavelength').setValue(ai.wavelength)
        finally:
            self.setSilence(False)



    def addDevice(self, device):
        if device:
            try:
                self.setSilence(True)
                devicechild = DeviceParameter(device)
                self.addChild(devicechild)
                ai = AzimuthalIntegrator(wavelength=self['Wavelength'])
                ai.detector = FastCCD()
                self.AIs[device] = ai
                self.multiAI.ais = list(self.AIs.values())
            finally:
                self.setSilence(False)

    def setModels(self, headermodel, selectionmodel):
        self.headermodel = headermodel
        self.headermodel.dataChanged.connect(self.dataChanged)
        self.selectionmodel = selectionmodel


    def dataChanged(self, start, end):
        currentIndex = self.selectionmodel.currentIndex()
        if currentIndex.isValid():
            # TODO-- remove hard-coding of stream
            stream = "primary"
            item = self.headermodel.item(self.selectionmodel.currentIndex().row())
            catalog = item.data(Qt.UserRole)  # type: Catalog
            fields = [technique["data_mapping"]["data_image"][1] for technique in catalog.metadata["techniques"] if
                      technique["technique"] == "scattering"]

            for field in fields:
                if field not in self.AIs:
                    self.addDevice(field)

    def wavelengthChanged(self):
        self.param('Energy').setValue(1.239842e-6 / self.param('Wavelength').value(), blockSignal=self.EnergyChanged)

    def energyChanged(self):
        self.param('Wavelength').setValue(1.239842e-6 / self.param('Energy').value(),
                                          blockSignal=self.WavelengthChanged)

    def toState(self):
        self.apply()
        return self.saveState(filter='user'), self.AIs

    def fromState(self, state):
        self.setSilence(True)
        try:
            self.AIs = state[1]
            for child in self.children()[2:]:
                child.remove()
            for name, ai in self.AIs.items():
                if name in state[0]['children']:
                    self.addDevice(name)
                    self.setAI(ai, name)

            self.restoreState(state[0], addChildren=False, removeChildren=False)
        except Exception as ex:
            msg.logError(ex)
        finally:
            self.setSilence(False)
