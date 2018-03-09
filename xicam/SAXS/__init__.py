import numpy as np
from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *

from . import patches


from xicam.core import msg
from xicam.core.data import load_header, NonDBHeader
from xicam.core.execution.workflow import Workflow

from xicam.plugins import GUIPlugin, GUILayout, manager as pluginmanager
from .calibration import CalibrationPanel
from .masking import MaskingPanel
from .widgets.SAXSMultiViewer import SAXSMultiViewerPlugin
from .widgets.SAXSViewerPlugin import SAXSViewerPlugin
from .widgets.SAXSToolbar import SAXSToolbar
from .widgets.SAXSSpectra import SAXSSpectra
from xicam.gui.widgets.linearworkfloweditor import WorkflowEditor
from pyFAI import AzimuthalIntegrator, detectors, calibrant

from xicam.gui.widgets.tabview import TabView, TabViewSynchronizer


# todo: flip pilatus data at read


class SAXSPlugin(GUIPlugin):
    name = 'SAXS'
    sigLog = Signal(int, str, str, np.ndarray)

    def __init__(self):
        self.headermodel = QStandardItemModel()
        self.calibrationtabview = TabView(self.headermodel,
                                          pluginmanager.getPluginByName('SAXSViewerPlugin',
                                                                        'WidgetPlugin').plugin_object,
                                          'pilatus2M_image')
        self.masktabview = TabView(self.headermodel,
                                   pluginmanager.getPluginByName('SAXSViewerPlugin', 'WidgetPlugin').plugin_object,
                                   'pilatus2M_image')
        self.reducetabview = TabView(self.headermodel,
                               pluginmanager.getPluginByName('SAXSViewerPlugin', 'WidgetPlugin').plugin_object,
                               'pilatus2M_image')
        self.comparemultiview = SAXSMultiViewerPlugin(self.headermodel)

        self.tabviewsynchronizer = TabViewSynchronizer(
            [self.calibrationtabview, self.masktabview, self.reducetabview, self.comparemultiview.leftTabView])
        self.toolbar = SAXSToolbar(self.calibrationtabview)
        self.calibrationsettings = pluginmanager.getPluginByName('DeviceProfiles', 'SettingsPlugin').plugin_object
        self.calibrationsettings.setModel(self.headermodel)
        self.calibrationpanel = CalibrationPanel()
        self.calibrationpanel.sigDoCalibrateWorkflow.connect(self.doCalibrateWorkflow)

        self.maskingworkflow = Workflow('Masking')
        self.maskeditor = WorkflowEditor(self.maskingworkflow)
        self.maskeditor.sigWorkflowChanged.connect(self.doMaskingWorkflow)

        self.stages = {
            'Calibrate': GUILayout(self.calibrationtabview,
                                   # pluginmanager.getPluginByName('SAXSViewerPlugin', 'WidgetPlugin').plugin_object()
                                   right=self.calibrationsettings.widget,
                                   rightbottom=self.calibrationpanel,
                                   top=self.toolbar),
            'Mask': GUILayout(self.masktabview,
                              right=self.maskeditor),
            'Reduce': GUILayout(self.reducetabview,
                                bottom=pluginmanager.getPluginByName('SAXSSpectra', 'WidgetPlugin').plugin_object()),
            'Compare': GUILayout(self.comparemultiview, top=self.toolbar, bottom=SAXSSpectra())
        }
        super(SAXSPlugin, self).__init__()

    def appendHeader(self, header: NonDBHeader, **kwargs):
        item = QStandardItem(header.startdoc.get('sample_name', '????'))
        item.header = header
        self.headermodel.appendRow(item)
        self.headermodel.dataChanged.emit(QModelIndex(), QModelIndex())

    def doCalibrateWorkflow(self, workflow: Workflow):
        data = self.calibrationtabview.currentWidget().header.meta_array('pilatus2M_image')[0]
        device = self.calibrationsettings.parameter['Device']
        ai = self.calibrationsettings.AI('pilatus2M')
        ai.detector = detectors.Pilatus2M()
        c = calibrant.ALL_CALIBRANTS('AgBh')

        def setAI(result):
            self.calibrationsettings.setAI(result['ai'].value, device)

        workflow.execute(None, data=data, ai=ai, calibrant=c, callback_slot=setAI)

    def doMaskingWorkflow(self, workflow: Workflow):
        data = self.calibrationtabview.currentWidget().header.meta_array('pilatus2M_image')[0]
        ai = self.calibrationsettings.AI('pilatus2M')
        ai.detector = detectors.Pilatus2M()
        outputwidget = self.masktabview.currentWidget()

        def showMask(result):
            outputwidget.setMaskImage(result['mask'].value)

        workflow.execute(None, data=data, callback_slot=showMask)
