import numpy as np
from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *

from xicam.core import msg
from xicam.core.data import load_header, NonDBHeader
from xicam.core.execution.workflow import Workflow

from xicam.plugins import GUIPlugin, GUILayout, manager as pluginmanager
from xicam.SAXS.calibration import CalibrationPanel
from xicam.SAXS.widgets.SAXSMultiViewer import SAXSMultiViewerPlugin
from xicam.SAXS.widgets.SAXSViewerPlugin import SAXSViewerPlugin
from xicam.SAXS.widgets.SAXSToolbar import SAXSToolbar
from xicam.SAXS.widgets.SAXSSpectra import SAXSSpectra
from xicam.gui.widgets.linearworkfloweditor import WorkflowEditor
from xicam.SAXS.processing.workflows import ReduceWorkflow, DisplayWorkflow
from xicam.SAXS.calibration.workflows import SimulateWorkflow
from xicam.SAXS.masking.workflows import MaskingWorkflow
from pyFAI import AzimuthalIntegrator, detectors, calibrant
import pyqtgraph as pg
from functools import partial

from xicam.gui.widgets.tabview import TabView, TabViewSynchronizer


class SAXSPlugin(GUIPlugin):
    name = 'SAXS'

    def __init__(self):
        # Data model
        self.headermodel = QStandardItemModel()
        self.selectionmodel = QItemSelectionModel(self.headermodel)

        # Initialize workflows
        self.maskingworkflow = MaskingWorkflow()
        self.simulateworkflow = SimulateWorkflow()
        self.displayworkflow = DisplayWorkflow()
        self.reduceworkflow = ReduceWorkflow()

        # Grab the calibration plugin
        self.calibrationsettings = pluginmanager.getPluginByName('DeviceProfiles', 'SettingsPlugin').plugin_object

        # Setup TabViews
        self.calibrationtabview = TabView(self.headermodel, widgetcls=SAXSViewerPlugin,
                                          selectionmodel=self.selectionmodel,
                                          bindings=[('sigTimeChangeFinished', self.indexChanged),
                                                    (self.calibrationsettings.sigGeometryChanged, 'setGeometry')],
                                          geometry=self.getAI)
        self.masktabview = TabView(self.headermodel, widgetcls=SAXSViewerPlugin, selectionmodel=self.selectionmodel,
                                   bindings=[('sigTimeChangeFinished', self.indexChanged),
                                             (self.calibrationsettings.sigGeometryChanged, 'setGeometry')],
                                   geometry=self.getAI)
        self.reducetabview = TabView(self.headermodel, widgetcls=SAXSViewerPlugin, selectionmodel=self.selectionmodel,
                                     bindings=[('sigTimeChangeFinished', self.indexChanged),
                                               (self.calibrationsettings.sigGeometryChanged, 'setGeometry')],
                                     geometry=self.getAI)
        self.comparemultiview = SAXSMultiViewerPlugin(self.headermodel, self.selectionmodel)

        # self.tabviewsynchronizer = TabViewSynchronizer(
        #     [self.calibrationtabview, self.masktabview, self.reducetabview, self.comparemultiview.leftTabView])

        # Setup toolbars
        self.toolbar = SAXSToolbar(self.headermodel, self.selectionmodel, workflow=self.reduceworkflow)
        self.calibrationtabview.kwargs['toolbar'] = self.toolbar
        self.reducetabview.kwargs['toolbar'] = self.toolbar

        # Setup calibration widgets
        self.calibrationsettings.setModels(self.headermodel, self.calibrationtabview.selectionmodel)
        self.calibrationpanel = CalibrationPanel(self.headermodel, self.calibrationtabview.selectionmodel)
        self.calibrationpanel.sigDoCalibrateWorkflow.connect(self.doCalibrateWorkflow)

        # Setup masking widgets
        self.maskeditor = WorkflowEditor(self.maskingworkflow)
        self.maskeditor.sigWorkflowChanged.connect(self.doMaskingWorkflow)

        # Setup reduction widgets
        self.displayeditor = WorkflowEditor(self.displayworkflow)
        self.reduceeditor = WorkflowEditor(self.reduceworkflow)
        self.reduceplot = SAXSSpectra(self.reduceworkflow, self.toolbar)
        self.toolbar.sigDoWorkflow.connect(partial(self.doReduceWorkflow, self.reduceworkflow))
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
                                   top=self.toolbar),
            'Mask': GUILayout(self.masktabview,
                              right=self.maskeditor,
                              top=self.toolbar),
            'Reduce': GUILayout(self.reducetabview,
                                bottom=self.reduceplot, right=self.reduceeditor, righttop=self.displayeditor,
                                top=self.toolbar),
            'Compare': GUILayout(self.comparemultiview, top=self.toolbar, bottom=self.reduceplot,
                                 right=self.reduceeditor)
        }
        super(SAXSPlugin, self).__init__()

    # def experimentChanged(self):
    #     self.doReduceWorkflow(self.reduceworkflow)

    def getAI(self):
        """ Convenience method to get current field's AI """
        device = self.toolbar.detectorcombobox.currentText()
        ai = self.calibrationsettings.AI(device)
        return ai

    def indexChanged(self):
        if not self.reduceplot.toolbar.multiplot.isChecked():
            self.doReduceWorkflow(self.reduceworkflow)

    def appendHeader(self, header: NonDBHeader, **kwargs):
        item = QStandardItem(header.startdoc.get('sample_name', '????'))
        item.header = header
        self.headermodel.appendRow(item)
        self.selectionmodel.setCurrentIndex(self.headermodel.index(self.headermodel.rowCount() - 1, 0),
                                            QItemSelectionModel.Rows)
        self.headermodel.dataChanged.emit(QModelIndex(), QModelIndex())

    def doCalibrateWorkflow(self, workflow: Workflow):
        data = self.calibrationtabview.currentWidget().header.meta_array()[0]
        device = self.toolbar.detectorcombobox.currentText()
        ai = self.calibrationsettings.AI(device)
        # ai.detector = detectors.Pilatus2M()
        calibrant = self.calibrationpanel.parameter['Calibrant Material']

        def setAI(result):
            self.calibrationsettings.setAI(result['ai'].value, device)
            self.doMaskingWorkflow(self.maskingworkflow)

        workflow.execute(None, data=data, ai=ai, calibrant=calibrant, callback_slot=setAI, threadkey='calibrate')

    def doSimulateWorkflow(self, workflow: Workflow):
        data = self.calibrationtabview.currentWidget().header.meta_array()[0]
        device = self.toolbar.detectorcombobox.currentText()
        ai = self.calibrationsettings.AI(device)
        calibrant = self.calibrationpanel.parameter['Calibrant Material']
        outputwidget = self.calibrationtabview.currentWidget()

        def showSimulatedCalibrant(result=None):
            outputwidget.setCalibrantImage(result['data'].value)

        workflow.execute(None, data=data, ai=ai, calibrant=calibrant, callback_slot=showSimulatedCalibrant,
                         threadkey='simulate')

    def doMaskingWorkflow(self, workflow: Workflow):
        if not self.checkPolygonsSet(workflow):
            data = self.calibrationtabview.currentWidget().header.meta_array()[0]
            device = self.toolbar.detectorcombobox.currentText()
            ai = self.calibrationsettings.AI(device)
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
        data = currentwidget.header.meta_array()[currentwidget.timeIndex(currentwidget.timeLine)[0]]
        device = self.toolbar.detectorcombobox.currentText()
        ai = self.calibrationsettings.AI(device)
        mask = self.maskingworkflow.lastresult[0]['mask'].value if self.maskingworkflow.lastresult else None
        outputwidget = currentwidget

        def showDisplay(*results):
            outputwidget.setResults(results)

        workflow.execute(None, data=data, ai=ai, mask=mask, callback_slot=showDisplay, threadkey='display')

    def doReduceWorkflow(self, workflow: Workflow):
        multimode = self.reduceplot.toolbar.multiplot.isChecked()
        currentwidget = self.reducetabview.currentWidget()
        data = currentwidget.header.meta_array()
        if not multimode:
            data = [data[currentwidget.timeIndex(currentwidget.timeLine)[0]]]
        device = self.toolbar.detectorcombobox.currentText()
        ai = self.calibrationsettings.AI(device)
        ai = [ai] * len(data)
        mask = [self.maskingworkflow.lastresult[0]['mask'].value if self.maskingworkflow.lastresult else None] * len(
            data)
        outputwidget = self.reduceplot
        outputwidget.clear_all()

        def showReduce(*results):
            outputwidget.appendResult(results)

        workflow.execute_all(None, data=data, ai=ai, mask=mask, callback_slot=showReduce, threadkey='reduce')

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
