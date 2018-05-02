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
from .widgets.SAXSMultiViewer import SAXSMultiViewerPlugin
from .widgets.SAXSViewerPlugin import SAXSViewerPlugin
from .widgets.SAXSToolbar import SAXSToolbar
from .widgets.SAXSSpectra import SAXSSpectra
from xicam.gui.widgets.linearworkfloweditor import WorkflowEditor
from .processing.workflows import ReduceWorkflow, DisplayWorkflow
from .calibration.workflows import SimulateWorkflow
from .masking.workflows import MaskingWorkflow
from pyFAI import AzimuthalIntegrator, detectors, calibrant
import pyqtgraph as pg
from functools import partial

from xicam.gui.widgets.tabview import TabView, TabViewSynchronizer


# todo: flip pilatus data at read


class SAXSPlugin(GUIPlugin):
    name = 'SAXS'
    sigLog = Signal(int, str, str, np.ndarray)

    def __init__(self):
        # Data model
        self.headermodel = QStandardItemModel()

        # Setup TabViews
        self.calibrationtabview = TabView(self.headermodel,
                                          pluginmanager.getPluginByName('SAXSViewerPlugin',
                                                                        'WidgetPlugin').plugin_object,
                                          'primary')
        self.masktabview = TabView(self.headermodel,
                                   pluginmanager.getPluginByName('SAXSViewerPlugin', 'WidgetPlugin').plugin_object,
                                   'primary')
        self.reducetabview = TabView(self.headermodel,
                                     pluginmanager.getPluginByName('SAXSViewerPlugin', 'WidgetPlugin').plugin_object,
                                     'primary')
        self.comparemultiview = SAXSMultiViewerPlugin(self.headermodel)

        self.tabviewsynchronizer = TabViewSynchronizer(
            [self.calibrationtabview, self.masktabview, self.reducetabview, self.comparemultiview.leftTabView])

        # Setup toolbars
        self.calibrationtoolbar = SAXSToolbar(self.calibrationtabview)
        self.reducetoolbar = SAXSToolbar(self.reducetabview)
        self.calibrationtabview.kwargs['toolbar'] = self.calibrationtoolbar
        self.reducetabview.kwargs['toolbar'] = self.reducetoolbar

        # Setup calibration widgets
        self.calibrationsettings = pluginmanager.getPluginByName('DeviceProfiles', 'SettingsPlugin').plugin_object
        self.calibrationsettings.setModels(self.headermodel, self.calibrationtabview.selectionmodel)
        self.calibrationpanel = CalibrationPanel()
        self.calibrationpanel.setModels(self.headermodel, self.calibrationtabview.selectionmodel)
        self.calibrationpanel.sigDoCalibrateWorkflow.connect(self.doCalibrateWorkflow)

        # Setup masking widgets
        self.maskingworkflow = MaskingWorkflow()
        self.maskeditor = WorkflowEditor(self.maskingworkflow)
        self.maskeditor.sigWorkflowChanged.connect(self.doMaskingWorkflow)

        # Setup reduction widgets
        self.simulateworkflow = SimulateWorkflow()
        self.displayworkflow = DisplayWorkflow()
        self.displayeditor = WorkflowEditor(self.displayworkflow)
        self.reduceworkflow = ReduceWorkflow()
        self.reduceworkflow.attach(partial(self.doReduceWorkflow, self.reduceworkflow))
        self.reduceeditor = WorkflowEditor(self.reduceworkflow)
        self.reduceplot = pluginmanager.getPluginByName('SAXSSpectra', 'WidgetPlugin').plugin_object(
            self.reduceworkflow)
        self.reduceeditor.sigWorkflowChanged.connect(self.doReduceWorkflow)
        self.displayeditor.sigWorkflowChanged.connect(self.doDisplayWorkflow)
        self.reducetabview.currentChanged.connect(partial(self.doReduceWorkflow, self.reduceworkflow))
        self.reducetabview.currentChanged.connect(partial(self.doDisplayWorkflow, self.displayworkflow))

        # Setup more bindings
        self.calibrationsettings.sigSimulateCalibrant.connect(partial(self.doSimulateWorkflow, self.simulateworkflow))

        self.stages = {
            'Calibrate': GUILayout(self.calibrationtabview,
                                   # pluginmanager.getPluginByName('SAXSViewerPlugin', 'WidgetPlugin').plugin_object()
                                   right=self.calibrationsettings.widget,
                                   rightbottom=self.calibrationpanel,
                                   top=self.calibrationtoolbar),
            'Mask': GUILayout(self.masktabview,
                              right=self.maskeditor),
            'Reduce': GUILayout(self.reducetabview,
                                bottom=self.reduceplot, right=self.reduceeditor, righttop=self.displayeditor,
                                top=self.reducetoolbar),
            'Compare': GUILayout(self.comparemultiview, top=self.reducetoolbar, bottom=SAXSSpectra(self.reduceworkflow))
        }
        super(SAXSPlugin, self).__init__()

    def appendHeader(self, header: NonDBHeader, **kwargs):
        item = QStandardItem(header.startdoc.get('sample_name', '????'))
        item.header = header
        self.headermodel.appendRow(item)
        self.headermodel.dataChanged.emit(QModelIndex(), QModelIndex())

    def doCalibrateWorkflow(self, workflow: Workflow):
        data = self.calibrationtabview.currentWidget().header.meta_array('primary')[0]
        device = self.calibrationpanel.parameter['Device']
        ai = self.calibrationsettings.AI('pilatus2M')
        ai.detector = detectors.Pilatus2M()
        c = calibrant.ALL_CALIBRANTS('AgBh')

        def setAI(result):
            self.calibrationsettings.setAI(result['ai'].value, device)
            self.doMaskingWorkflow(self.maskingworkflow)

        workflow.execute(None, data=data, ai=ai, calibrant=c, callback_slot=setAI, threadkey='calibrate')

    def doSimulateWorkflow(self, workflow: Workflow):
        data = self.calibrationtabview.currentWidget().header.meta_array('primary')[0]
        ai = self.calibrationsettings.AI('pilatus2M')
        ai.detector = detectors.Pilatus2M()
        calibrant = self.calibrationpanel.parameter['Calibrant Material']
        outputwidget = self.calibrationtabview.currentWidget()

        def showSimulatedCalibrant(result=None):
            outputwidget.setCalibrantImage(result['data'].value)

        workflow.execute(None, data=data, ai=ai, calibrant=calibrant, callback_slot=showSimulatedCalibrant,
                         threadkey='simulate')

    def doMaskingWorkflow(self, workflow: Workflow):
        if not self.checkPolygonsSet(workflow):
            data = self.calibrationtabview.currentWidget().header.meta_array('primary')[0]
            ai = self.calibrationsettings.AI('pilatus2M')
            ai.detector = detectors.Pilatus2M()
            outputwidget = self.masktabview.currentWidget()

            def showMask(result=None):
                if result:
                    outputwidget.setMaskImage(result['mask'].value)
                else:
                    outputwidget.setMaskImage(None)
                self.doDisplayWorkflow(self.displayworkflow)
                self.doReduceWorkflow(self.reduceworkflow)

            workflow.execute(None, data=data, ai=ai, callback_slot=showMask, threadkey='masking')

    def doDisplayWorkflow(self, workflow: Workflow):
        currentwidget = self.reducetabview.currentWidget()
        data = currentwidget.header.meta_array('primary')[currentwidget.timeIndex(currentwidget.timeLine)[0]]
        ai = self.calibrationsettings.AI('pilatus2M')
        ai.detector = detectors.Pilatus2M()
        mask = self.maskingworkflow.lastresult[0]['mask'].value if self.maskingworkflow.lastresult else None
        outputwidget = currentwidget

        def showDisplay(*results):
            outputwidget.setResults(results)

        workflow.execute(None, data=data, ai=ai, mask=mask, callback_slot=showDisplay, threadkey='display')

    def doReduceWorkflow(self, workflow: Workflow):
        currentwidget = self.reducetabview.currentWidget()
        data = currentwidget.header.meta_array('primary')[currentwidget.timeIndex(currentwidget.timeLine)[0]]
        ai = self.calibrationsettings.AI('pilatus2M')
        ai.detector = detectors.Pilatus2M()
        mask = self.maskingworkflow.lastresult[0]['mask'].value if self.maskingworkflow.lastresult else None
        outputwidget = self.reduceplot

        def showReduce(*results):
            outputwidget.clear()
            outputwidget.setResults(results)

        workflow.execute(None, data=data, ai=ai, mask=mask, callback_slot=showReduce, threadkey='reduce')

    def checkPolygonsSet(self, workflow: Workflow):
        """
        Check for any unset polygonmask processes; start masking mode if found

        Parameters
        ----------
        workflow: Workflow

        Returns
        -------
        bool
            True if unset polygonmask process is found

        """
        pluginmaskclass = pluginmanager.getPluginByName('Polygon Mask', 'ProcessingPlugin')
        for process in workflow.processes:
            if isinstance(process, pluginmaskclass.plugin_object):
                if process.polygon.value is None:
                    self.startPolygonMasking(process)
                    return True
        return False

    def startPolygonMasking(self, process):
        self.setEnabledOuterWidgets(False)

        # Start drawing mode
        viewer = self.masktabview.currentWidget()  # type: SAXSViewerPlugin
        viewer.imageItem.setDrawKernel(kernel=np.array([[0]]), mask=None, center=(0, 0), mode='add')
        viewer.imageItem.drawMode = self.drawEvent
        viewer.maskROI.clearPoints()

        # Setup other signals
        process.parameter.child('Finish Mask').sigActivated.connect(partial(self.finishMask, process))
        process.parameter.child('Clear Selection').sigActivated.connect(self.clearMask)

    def setEnabledOuterWidgets(self, enabled):
        # Disable other widgets
        mainwindow = self.masktabview.window()
        for dockwidget in mainwindow.findChildren(QDockWidget):
            dockwidget.setEnabled(enabled)
        mainwindow.rightwidget.setEnabled(True)
        self.maskeditor.workflowview.setEnabled(enabled)
        self.masktabview.tabBar().setEnabled(enabled)
        mainwindow.menuBar().setEnabled(enabled)
        mainwindow.pluginmodewidget.setEnabled(enabled)

    def clearMask(self):
        viewer = self.masktabview.currentWidget()  # type: SAXSViewerPlugin
        viewer.maskROI.clearPoints()

    def finishMask(self, process, sender):
        viewer = self.masktabview.currentWidget()  # type: SAXSViewerPlugin
        process.polygon.value = np.array([list(handle['pos']) for handle in viewer.maskROI.handles])
        self.setEnabledOuterWidgets(True)

        # End drawing mode
        viewer.imageItem.drawKernel = None
        viewer.maskROI.clearPoints()
        process.parameter.clearChildren()

        # Redo workflow with polygon
        self.doMaskingWorkflow(process._workflow)

    def drawEvent(self, kernel, imgdata, mask, ss, ts, event):
        viewer = self.masktabview.currentWidget()  # type: SAXSViewerPlugin
        viewer.maskROI.addFreeHandle(viewer.view.vb.mapSceneToView(event.scenePos()))
        if len(viewer.maskROI.handles) > 1:
            viewer.maskROI.addSegment(viewer.maskROI.handles[-2]['item'], viewer.maskROI.handles[-1]['item'])
