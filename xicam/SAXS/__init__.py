import numpy as np
from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *

from . import patches


from xicam.core import msg
from xicam.core.data import load_header, NonDBHeader

from xicam.plugins import GUIPlugin, GUILayout, manager as pluginmanager
from .calibration import CalibrationPanel
from .masking import MaskingPanel
from .widgets.SAXSMultiViewer import SAXSMultiViewerPlugin
from .widgets.SAXSViewerPlugin import SAXSViewerPlugin
from .widgets.SAXSToolbar import SAXSToolbar
from .widgets.SAXSSpectra import SAXSSpectra
from pyFAI import AzimuthalIntegrator, detectors, calibrant

from xicam.gui.widgets.tabview import TabView


class SAXSPlugin(GUIPlugin):
    name = 'SAXS'
    sigLog = Signal(int, str, str, np.ndarray)

    def __init__(self):
        self.headermodel = QStandardItemModel()
        self.tabview = TabView(self.headermodel,
                               pluginmanager.getPluginByName('SAXSViewerPlugin', 'WidgetPlugin').plugin_object,
                               'pilatus2M_image')
        self.toolbar = SAXSToolbar(self.tabview)
        pluginmanager.getPluginByName('DeviceProfiles', 'SettingsPlugin').plugin_object.setModel(self.headermodel)
        self.calibrationpanel = CalibrationPanel()
        self.calibrationpanel.sigDoWorkflow.connect(self.doWorkflow)

        self.stages = {
            'Calibrate': GUILayout(self.tabview,
                                   # pluginmanager.getPluginByName('SAXSViewerPlugin', 'WidgetPlugin').plugin_object()
                                   right=pluginmanager.getPluginByName('DeviceProfiles',
                                                                       'SettingsPlugin').plugin_object.widget,
                                   rightbottom=self.calibrationpanel,
                                   top=self.toolbar),
            'Mask': GUILayout(self.tabview,
                              right=MaskingPanel()),
            'Reduce': GUILayout(QLabel('Reduce'),
                                bottom=pluginmanager.getPluginByName('SAXSSpectra', 'WidgetPlugin').plugin_object()),
            'Compare': GUILayout(SAXSMultiViewerPlugin(self.headermodel), top=self.toolbar, bottom=SAXSSpectra())
        }
        super(SAXSPlugin, self).__init__()

    def appendHeader(self, header: NonDBHeader, **kwargs):
        item = QStandardItem(header.startdoc.get('sample_name', '????'))
        item.header = header
        self.headermodel.appendRow(item)
        self.headermodel.dataChanged.emit(QModelIndex(), QModelIndex())

    def doWorkflow(self, workflow):
        data = self.tabview.currentWidget().header.meta_array('pilatus2M_image')[0]
        ai = AzimuthalIntegrator()
        ai.set_wavelength(124e-12)
        ai.detector = detectors.Pilatus2M()
        c = calibrant.ALL_CALIBRANTS('AgBh')

        print(workflow.execute(None, data=data, ai=ai, calibrant=c)[0]['ai'].value.getFit2D())
