import numpy as np
from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *

import cloudpickle as pickle

from databroker.core import BlueskyRun
from pyqtgraph.parametertree import Parameter, ParameterTree
from pyqtgraph.parametertree.parameterTypes import ListParameter

from xicam.core import msg, threads
from xicam.core.data import load_header, NonDBHeader
from xicam.core.execution.workflow import Workflow

from xicam.plugins import GUIPlugin, GUILayout, manager as pluginmanager

from xicam.gui import static
from xicam.gui.widgets.imageviewmixins import PolygonROI
from xicam.gui.widgets.linearworkfloweditor import WorkflowEditor
from xicam.SAXS.processing.workflows import ReduceWorkflow, DisplayWorkflow
from xicam.SAXS.calibration.workflows import SimulateWorkflow
from xicam.SAXS.masking.workflows import MaskingWorkflow
from xicam.SAXS.widgets.SAXSViewerPlugin import SAXSViewerPluginBase
from pyFAI import AzimuthalIntegrator, detectors, calibrant
import pyqtgraph as pg
from functools import partial

from xicam.gui.widgets.tabview import TabView, TabViewSynchronizer

from xicam.SAXS.widgets.views import CorrelationWidget, FileSelectionView, OneTimeWidget, TwoTimeWidget
from xicam.SAXS.workflows.xpcs import FourierAutocorrelator, OneTime, TwoTime


class BlueskyItem(QStandardItem):

    def __init__(self):
        super(QStandardItem, self).__init__()


class XPCSViewerPlugin(PolygonROI, SAXSViewerPluginBase):
    pass


class XPCSProcessor(ParameterTree):
    def __init__(self, *args, **kwargs):
        super(XPCSProcessor, self).__init__()
        self._paramName = 'Algorithm'
        self._name = 'XPCS Processor'
        self.workflow = None
        self.param = None
        self._workflows = dict()

        self.listParameter = ListParameter(name=self._paramName,
                                           values={'':''},
                                           value='')

        self.param = Parameter(children=[self.listParameter], name=self._name)
        self.setParameters(self.param, showTop=False)

    def update(self, *_):
        for child in self.param.childs[1:]:
            child.remove()

        self.workflow = self._workflows.get(self.listParameter.value().name, self.listParameter.value()())
        self._workflows[self.workflow.name] = self.workflow
        for process in self.workflow.processes:
            self.param.addChild(process.parameter)


class OneTimeProcessor(XPCSProcessor):
    def __init__(self, *args, **kwargs):
        super(OneTimeProcessor, self).__init__()
        self._name = '1-Time Processor'
        self.listParameter.setLimits(OneTimeAlgorithms.algorithms())
        self.listParameter.setValue(OneTimeAlgorithms.algorithms()[OneTimeAlgorithms.default()])

        self.update()
        self.listParameter.sigValueChanged.connect(self.update)


class TwoTimeProcessor(XPCSProcessor):
    def __init__(self, *args, **kwargs):
        super(TwoTimeProcessor, self).__init__()
        self._name = '2-Time Processor'
        self.listParameter.setLimits(TwoTimeAlgorithms.algorithms())
        self.listParameter.setValue(TwoTimeAlgorithms.algorithms()[TwoTimeAlgorithms.default()])

        self.update()
        self.listParameter.sigValueChanged.connect(self.update)


class ProcessingAlgorithms:
    """
    Convenience class to get the available algorithms that can be used for
    one-time and two-time correlations.
    """
    @staticmethod
    def algorithms():
        return {
            TwoTimeAlgorithms.name: TwoTimeAlgorithms.algorithms(),
            OneTimeAlgorithms.name: OneTimeAlgorithms.algorithms()
        }


class TwoTimeAlgorithms(ProcessingAlgorithms):
    name = '2-Time Algorithms'
    @staticmethod
    def algorithms():
        return {TwoTime.name: TwoTime}

    @staticmethod
    def default():
        return TwoTime.name


class OneTimeAlgorithms(ProcessingAlgorithms):
    name = '1-Time Algorithms'
    @staticmethod
    def algorithms():
        return {OneTime.name: OneTime,
                FourierAutocorrelator.name: FourierAutocorrelator}

    @staticmethod
    def default():
        return OneTime.name



class SAXSPlugin(GUIPlugin):
    name = 'SAXS'

    def __init__(self):
        # Late imports required due to plugin system
        from xicam.SAXS.calibration import CalibrationPanel
        from xicam.SAXS.widgets.SAXSMultiViewer import SAXSMultiViewerPlugin
        from xicam.SAXS.widgets.SAXSViewerPlugin import SAXSViewerPluginBase, SAXSCalibrationViewer, SAXSMaskingViewer, \
            SAXSReductionViewer
        from xicam.SAXS.widgets.SAXSToolbar import SAXSToolbarRaw, SAXSToolbarMask, SAXSToolbarReduce
        from xicam.SAXS.widgets.SAXSSpectra import SAXSSpectra

        self.derivedDataModel = QStandardItemModel()
        self.catalogModel = QStandardItemModel()

        # Data model
        self.headermodel = QStandardItemModel()
        self.selectionmodel = QItemSelectionModel(self.headermodel)

        # Initialize workflows
        self.maskingworkflow = MaskingWorkflow()
        self.simulateworkflow = SimulateWorkflow()
        self.displayworkflow = DisplayWorkflow()
        self.reduceworkflow = ReduceWorkflow()

        # Grab the calibration plugin
        self.calibrationsettings = pluginmanager.getPluginByName('xicam.SAXS.calibration',
                                                                 'SettingsPlugin').plugin_object

        # Setup TabViews
        self.calibrationtabview = TabView(self.headermodel, widgetcls=SAXSCalibrationViewer,
                                          selectionmodel=self.selectionmodel,
                                          bindings=[(self.calibrationsettings.sigGeometryChanged, 'setGeometry')],
                                          geometry=self.getAI)
        self.masktabview = TabView(self.headermodel, widgetcls=SAXSMaskingViewer, selectionmodel=self.selectionmodel,
                                   bindings=[('sigTimeChangeFinished', self.indexChanged),
                                             (self.calibrationsettings.sigGeometryChanged, 'setGeometry')],
                                   geometry=self.getAI)
        self.reducetabview = TabView(self.headermodel, widgetcls=SAXSReductionViewer,
                                     selectionmodel=self.selectionmodel,
                                     bindings=[('sigTimeChangeFinished', self.indexChanged),
                                               (self.calibrationsettings.sigGeometryChanged, 'setGeometry')],
                                     geometry=self.getAI)
        self.comparemultiview = SAXSMultiViewerPlugin(self.headermodel, self.selectionmodel)

        # Setup correlation views
        self.twoTimeView = TwoTimeWidget()
        self.twoTimeFileSelection = FileSelectionView(self.headermodel, self.selectionmodel)
        self.twoTimeProcessor = TwoTimeProcessor()
        self.twoTimeToolBar = QToolBar()
        self.twoTimeToolBar.addAction(QIcon(static.path('icons/run.png')), 'Process', self.processTwoTime)
        self.twoTimeToolBar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

        self.oneTimeView = OneTimeWidget()
        self.oneTimeFileSelection = FileSelectionView(self.headermodel, self.selectionmodel)
        self.oneTimeProcessor = OneTimeProcessor()
        self.oneTimeToolBar = QToolBar()
        self.oneTimeToolBar.addAction(QIcon(static.path('icons/run.png')), 'Process', self.processOneTime)
        self.oneTimeToolBar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

        # self.tabviewsynchronizer = TabViewSynchronizer(
        #     [self.calibrationtabview, self.masktabview, self.reducetabview, self.comparemultiview.leftTabView])

        # Setup toolbars
        self.rawtoolbar = SAXSToolbarRaw(self.headermodel, self.selectionmodel)
        self.masktoolbar = SAXSToolbarMask(self.headermodel, self.selectionmodel)
        self.reducetoolbar = SAXSToolbarReduce(self.headermodel, self.selectionmodel)
        self.reducetabview.kwargs['toolbar'] = self.reducetoolbar
        self.reducetoolbar.sigDeviceChanged.connect(self.deviceChanged)

        # Setup calibration widgets
        self.calibrationsettings.setModels(self.headermodel, self.calibrationtabview.selectionmodel)
        self.calibrationpanel = CalibrationPanel(self.headermodel, self.calibrationtabview.selectionmodel)
        self.calibrationpanel.sigDoCalibrateWorkflow.connect(self.doCalibrateWorkflow)
        self.calibrationsettings.sigGeometryChanged.connect(self.doSimulateWorkflow)

        # Setup masking widgets
        self.maskeditor = WorkflowEditor(self.maskingworkflow)
        self.maskeditor.sigWorkflowChanged.connect(self.doMaskingWorkflow)

        # Setup reduction widgets
        self.displayeditor = WorkflowEditor(self.displayworkflow)
        self.reduceeditor = WorkflowEditor(self.reduceworkflow)
        self.reduceplot = SAXSSpectra(self.reduceworkflow, self.reducetoolbar)
        self.reducetoolbar.sigDoWorkflow.connect(partial(self.doReduceWorkflow))
        self.reduceeditor.sigWorkflowChanged.connect(self.doReduceWorkflow)
        self.displayeditor.sigWorkflowChanged.connect(self.doDisplayWorkflow)
        self.reducetabview.currentChanged.connect(self.headerChanged)
        self.reducetabview.currentChanged.connect(self.headerChanged)

        self.stages = {
            'Calibrate': GUILayout(self.calibrationtabview,
                                   # pluginmanager.getPluginByName('SAXSViewerPlugin', 'WidgetPlugin').plugin_object()
                                   right=self.calibrationsettings.widget,
                                   rightbottom=self.calibrationpanel,
                                   top=self.rawtoolbar),
            'Mask': GUILayout(self.masktabview,
                              right=self.maskeditor,
                              top=self.masktoolbar),
            'Reduce': GUILayout(self.reducetabview,
                                bottom=self.reduceplot, right=self.reduceeditor, righttop=self.displayeditor,
                                top=self.reducetoolbar),
            'Compare': GUILayout(self.comparemultiview, top=self.reducetoolbar, bottom=self.reduceplot,
                                 right=self.reduceeditor),
            'Correlate': {
                '2-Time Correlation': GUILayout(self.twoTimeView,
                                                top=self.twoTimeToolBar,
                                                right=self.twoTimeFileSelection,
                                                rightbottom=self.twoTimeProcessor, ),
                # bottom=self.placeholder),
                '1-Time Correlation': GUILayout(self.oneTimeView,
                                                top=self.oneTimeToolBar,
                                                right=self.oneTimeFileSelection,
                                                rightbottom=self.oneTimeProcessor, )
            }
            # bottom=self.placeholder)
        }
        # TODO -- improve result caching
        self._results = []

        super(SAXSPlugin, self).__init__()

        # Start visualizations
        self.displayworkflow.visualize(self.reduceplot, imageview=lambda: self.reducetabview.currentWidget(),
                                       toolbar=self.reducetoolbar)

    # def experimentChanged(self):
    #     self.doReduceWorkflow(self.reduceworkflow)

    def getAI(self):
        """ Convenience method to get current field's AI """
        device = self.reducetoolbar.detectorcombobox.currentText()
        ai = self.calibrationsettings.AI(device)
        return ai

    def indexChanged(self):
        if not self.reduceplot.toolbar.multiplot.isChecked():
            self.doReduceWorkflow(self.reduceworkflow)

    def headerChanged(self):
        # TODO: both headerchanged and devicechanged will fire, redundantly, when the first image is opened
        self.doReduceWorkflow()
        self.doDisplayWorkflow()

    def deviceChanged(self, device_name):
        self.doReduceWorkflow()
        self.doDisplayWorkflow()

    def currentheader(self):
        return self.headerModel.itemFromIndex(self.selectionModel.currentIndex()).header

    def currentheaders(self):
        selected_indices = self.selectionModel.selectedIndexes()
        headers = []
        for model_index in selected_indices:
            headers.append(self.headerModel.itemFromIndex(model_index).header)
        return headers

    def appendCatalog(self, catalog: BlueskyRun, **kwargs):
        displayName = ""
        if 'sample_name' in catalog.metadata['start']:
            displayName = catalog.metadata['start']['sample_name']
        elif 'scan_id' in catalog.metadata['start']:
            displayName = catalog.metadata['start']['scan_id']
        else:
            displayName = catalog.metadata['start']['uid']

        item = BlueskyItem(displayName)
        item.setData(catalog, Qt.UserRole)
        self.catalogModel.appendRow(item)
        self.catalogModel.dataChanged.emit(item.index(), item.index())

    def appendHeader(self, header: NonDBHeader, **kwargs):
        item = QStandardItem(header.startdoc.get('sample_name', '????'))
        item.header = header
        self.headermodel.appendRow(item)
        index = self.headermodel.index(self.headermodel.rowCount() - 1, 0)
        self.selectionmodel.setCurrentIndex(index,
                                            QItemSelectionModel.Rows)
        self.headermodel.dataChanged.emit(index, index)
        # self.doSimulateWorkflow()

        # Load any reduced (processed) data
        reduced = False
        for descriptor in header.descriptordocs:
            if descriptor['name'] == '1-Time':
                reduced = True
                break
        paths = header.startdoc.get('paths')
        for path in paths:
            if reduced:
                startItem = QStandardItem(header.startdoc.get('sample_name', '??'))
                eventlist = header.eventdocs
                for event in eventlist:
                    eventItem = QStandardItem(repr(event['data']['dqlist']))
                    eventItem.setData(event, Qt.UserRole)
                    eventItem.setCheckable(True)
                    startItem.appendRow(eventItem)
                # TODO -- properly add to view (one-time or 2-time, etc.)
                self.oneTimeView.model.invisibleRootItem().appendRow(startItem)

    @threads.method()
    def doCalibrateWorkflow(self, workflow: Workflow):
        data = self.calibrationtabview.currentWidget().header.meta_array()[0]
        device = self.rawtoolbar.detectorcombobox.currentText()
        ai = self.calibrationsettings.AI(device)
        # ai.detector = detectors.Pilatus2M()
        calibrant = self.calibrationpanel.parameter['Calibrant Material']

        def setAI(result):
            self.calibrationsettings.setAI(result['ai'].value, device)
            self.doMaskingWorkflow()

        workflow.execute(None, data=data, ai=ai, calibrant=calibrant, callback_slot=setAI, threadkey='calibrate')

    @threads.method()
    def doSimulateWorkflow(self):
        # TEMPORARY HACK for demonstration
        if self.reducetabview.currentWidget():
            self.reducetabview.currentWidget().setTransform()

        if not self.calibrationtabview.currentWidget(): return
        data = self.calibrationtabview.currentWidget().header.meta_array()[0]
        device = self.rawtoolbar.detectorcombobox.currentText()
        ai = self.calibrationsettings.AI(device)
        if not ai: return
        calibrant = self.calibrationpanel.parameter['Calibrant Material']
        outputwidget = self.calibrationtabview.currentWidget()

        def showSimulatedCalibrant(result=None):
            outputwidget.setCalibrantImage(result['data'].value)

        self.simulateworkflow.execute(None, data=data, ai=ai, calibrant=calibrant, callback_slot=showSimulatedCalibrant,
                                      threadkey='simulate')

    @threads.method()
    def doMaskingWorkflow(self, workflow=None):
        if not self.masktabview.currentWidget(): return
        if not self.checkPolygonsSet(self.maskingworkflow):
            data = self.masktabview.currentWidget().header.meta_array()[0]
            device = self.masktoolbar.detectorcombobox.currentText()
            ai = self.calibrationsettings.AI(device)
            outputwidget = self.masktabview.currentWidget()

            def showMask(result=None):
                if result:
                    outputwidget.setMaskImage(result['mask'].value)
                else:
                    outputwidget.setMaskImage(None)
                self.doDisplayWorkflow()
                self.doReduceWorkflow()

            if not workflow: workflow = self.maskingworkflow
            workflow.execute(None, data=data, ai=ai, callback_slot=showMask, threadkey='masking')

    # disabled
    @threads.method()
    def doDisplayWorkflow(self):
        return
        if not self.reducetabview.currentWidget(): return
        currentwidget = self.reducetabview.currentWidget()
        data = currentwidget.header.meta_array()[currentwidget.timeIndex(currentwidget.timeLine)[0]]
        device = self.reducetoolbar.detectorcombobox.currentText()
        ai = self.calibrationsettings.AI(device)
        if not ai: return
        mask = self.maskingworkflow.lastresult[0]['mask'].value if self.maskingworkflow.lastresult else None
        outputwidget = currentwidget

        def showDisplay(*results):
            outputwidget.setResults(results)

        self.displayworkflow.execute(None, data=data, ai=ai, mask=mask, callback_slot=showDisplay, threadkey='display')

    @threads.method()
    def doReduceWorkflow(self):
        if not self.reducetabview.currentWidget(): return
        multimode = self.reduceplot.toolbar.multiplot.isChecked()
        currentwidget = self.reducetabview.currentWidget()
        data = currentwidget.header.meta_array()
        if not multimode:
            data = [data[currentwidget.timeIndex(currentwidget.timeLine)[0]]]
        device = self.reducetoolbar.detectorcombobox.currentText()
        ai = self.calibrationsettings.AI(device)
        if not ai: return
        ai = [ai] * len(data)
        mask = [self.maskingworkflow.lastresult[0]['mask'].value if self.maskingworkflow.lastresult else None] * len(
            data)
        outputwidget = self.reduceplot

        # outputwidget.clear_all()

        def showReduce(*results):
            self.reduceplot.plot_mode(results)
            pass

        self.reduceworkflow.execute_all(None, data=data, ai=ai, mask=mask, callback_slot=showReduce, threadkey='reduce')

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
        viewer = self.masktabview.currentWidget()  # type: SAXSViewerPluginBase
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
        viewer = self.masktabview.currentWidget()  # type: SAXSViewerPluginBase
        viewer.maskROI.clearPoints()

    def finishMask(self, process, sender):
        viewer = self.masktabview.currentWidget()  # type: SAXSViewerPluginBase
        process.polygon.value = np.array([list(handle['pos']) for handle in viewer.maskROI.handles])
        self.setEnabledOuterWidgets(True)

        # End drawing mode
        viewer.imageItem.drawKernel = None
        viewer.maskROI.clearPoints()
        process.parameter.clearChildren()

        # Redo workflow with polygon
        self.doMaskingWorkflow()

    def drawEvent(self, kernel, imgdata, mask, ss, ts, event):
        viewer = self.masktabview.currentWidget()  # type: SAXSViewerPluginBase
        viewer.maskROI.addFreeHandle(viewer.view.vb.mapSceneToView(event.scenePos()))
        if len(viewer.maskROI.handles) > 1:
            viewer.maskROI.addSegment(viewer.maskROI.handles[-2]['item'], viewer.maskROI.handles[-1]['item'])


    def processOneTime(self):
        canvas = self.oneTimeView.plot
        canvases = dict()  # Intentionally empty; unused in PlotHint
        self.process(self.oneTimeProcessor,
                     callback_slot=partial(self.saveResult, fileSelectionView=self.oneTimeFileSelection),
                     finished_slot=partial(self.updateDerivedDataModel,
                                           view=self.oneTimeView,
                                           canvas=canvas,
                                           canvases=canvases))

    def processTwoTime(self):
        canvas = None  # Intentionally empty; unused in ImageHint
        canvases = {"imageview": self.twoTimeView.image}
        self.process(self.twoTimeProcessor,
                     callback_slot=partial(self.saveResult, fileSelectionView=self.twoTimeFileSelection),
                     finished_slot=partial(self.updateDerivedDataModel,
                                           view=self.twoTimeView,
                                           canvas=canvas,
                                           canvases=canvases))

    def process(self, processor: XPCSProcessor, **kwargs):
        if processor:
            workflow = processor.workflow

            data = [header.meta_array() for header in self.currentheaders()]
            currentWidget = self.rawTabView.currentWidget()
            rois = [item for item in currentWidget.view.items if isinstance(item, BetterROI)]
            labels = [currentWidget.poly_mask()] * len(data)  # TODO: update for multiple ROIs
            numLevels = [1] * len(data)

            numBufs = []
            for i, _ in enumerate(data):
                shape = data[i].shape[0]
                # multi_tau_corr requires num_bufs to be even
                if shape % 2:
                    shape += 1
                numBufs.append(shape)

            if kwargs.get('callback_slot'):
                callbackSlot = kwargs['callback_slot']
            else:
                callbackSlot = self.saveResult
            if kwargs.get('finished_slot'):
                finishedSlot = kwargs['finished_slot']
            else:
                finishedSlot = self.updateDerivedDataModel

            workflowPickle = pickle.dumps(workflow)
            workflow.execute_all(None,
                                 data=data,
                                 labels=labels,
                                 num_levels=numLevels,
                                 num_bufs=numBufs,
                                 callback_slot=callbackSlot,
                                 finished_slot=partial(finishedSlot,
                                                       header=self.currentheader(),
                                                       roi=rois[0],  # todo -- handle multiple rois
                                                       workflow=workflow,
                                                       workflow_pickle=workflowPickle))

    def saveResult(self, result, fileSelectionView=None):
        if fileSelectionView:
            analyzed_results = dict()

            if not fileSelectionView.correlationName.displayText():
                analyzed_results['result_name'] = fileSelectionView.correlationName.placeholderText()
            else:
                analyzed_results['result_name'] = fileSelectionView.correlationName.displayText()
            analyzed_results = {**analyzed_results, **result}

            self._results.append(analyzed_results)

    def updateDerivedDataModel(self, view: CorrelationWidget, canvas, canvases, header, roi, workflow, workflow_pickle):
        parentItem = BlueskyItem(workflow.name)
        for hint in workflow.hints:
            item = BlueskyItem(hint.name)
            item.setData(hint, Qt.UserRole)
            item.setCheckable(True)
            parentItem.appendRow(item)
        self.derivedDataModel.appendRow(parentItem)