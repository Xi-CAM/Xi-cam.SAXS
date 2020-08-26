from functools import partial

from databroker.core import BlueskyRun
import numpy as np
from qtpy.QtCore import QItemSelectionModel, Qt
from qtpy.QtGui import QStandardItemModel
from qtpy.QtWidgets import QDockWidget, QLabel
from xarray import DataArray

from xicam.core import msg, threads
from xicam.core.data import MetaXArray
from xicam.core.execution.workflow import Workflow
from xicam.plugins import GUIPlugin, GUILayout, manager as pluginmanager
from xicam.gui.widgets.linearworkfloweditor import WorkflowEditor
from xicam.gui.widgets.tabview import TabView

from .calibration.workflows import SimulateWorkflow
from .masking.workflows import MaskingWorkflow
from .processing.workflows import ReduceWorkflow, DisplayWorkflow
from .widgets.items import CheckableItem
from .widgets.parametertrees import CorrelationParameterTree, OneTimeParameterTree, TwoTimeParameterTree
from .widgets.SAXSViewerPlugin import SAXSViewerPluginBase
from .widgets.views import ResultsWidget
# TODO rename/move the data module
from .data.ensemble import EnsembleModel
from .workflows.roi import ROIWorkflow



class SAXSPlugin(GUIPlugin):
    name = 'SAXS'

    def __init__(self):
        # Late imports required due to plugin system
        from xicam.SAXS.calibration import CalibrationPanel
        from xicam.SAXS.widgets.SAXSViewerPlugin import SAXSCalibrationViewer, SAXSMaskingViewer, SAXSReductionViewer
        from xicam.SAXS.widgets.SAXSToolbar import SAXSToolbarRaw, SAXSToolbarMask, SAXSToolbarReduce
        from xicam.SAXS.widgets.XPCSToolbar import XPCSToolBar

#<<<<<<< Updated upstream
        self.derivedDataModel = EnsembleModel()
#=======
        # MODEL with Ensembles
        # Ensemble
            # RunCatalogs
                # Hints

        # Hints --> easily swappable with whatever databroker hint system is used eventually
        # a function call, extract_hints(catalog) -> [Hint]
        # eg. extract_hints(catalog_with_g2_curves) -> [PlotHint]
        # extract_hints needs to be context specific (e.g. nxXPCS) -> xpcs_extract_hints, uses assumed knowledge of the
        # keys in nexus that can be displayed in some way

        # ----------------------

        # (catalog),  interpret the projections in the catalog and return list of hints
        # filter (like projector does) to get the nxXPCS projection, and then give explicit hints based on the projection

        # Hint: whatever xicam thinks it needs to display things

        # TODO: [raw, raw_derived, internal_derived]
        #self.derivedDataModel = DerivedDataModel()
#>>>>>>> Stashed changes
        self.catalogModel = QStandardItemModel()

        # Data model
        self.catalogModel = QStandardItemModel()
        self.selectionmodel = QItemSelectionModel(self.catalogModel)

        # Initialize workflows
        self.maskingworkflow = MaskingWorkflow()
        self.simulateworkflow = SimulateWorkflow()
        self.displayworkflow = DisplayWorkflow()
        self.reduceworkflow = ReduceWorkflow()
        self.roiworkflow = ROIWorkflow()

        # Grab the calibration plugin
        self.calibrationsettings = pluginmanager.get_plugin_by_name('xicam.SAXS.calibration',
                                                                    'SettingsPlugin')

        # Setup TabViews
        # FIXME -- rework how fields propagate to displays (i.e. each image has its own detector, switching
        # between tabs updates the detector combobbox correctly)
        field = 'fast_ccd'
        self.calibrationtabview = TabView(self.catalogModel, widgetcls=SAXSCalibrationViewer,
                                          stream='primary', field=field,
                                          selectionmodel=self.selectionmodel,
                                          bindings=[(self.calibrationsettings.sigGeometryChanged, 'setGeometry')],
                                          geometry=self.getAI)
        self.masktabview = TabView(self.catalogModel, widgetcls=SAXSMaskingViewer, selectionmodel=self.selectionmodel,
                                   stream='primary', field=field,
                                   bindings=[('sigTimeChangeFinished', self.indexChanged),
                                             (self.calibrationsettings.sigGeometryChanged, 'setGeometry')],
                                   geometry=self.getAI)
        self.reducetabview = TabView(self.catalogModel, widgetcls=SAXSReductionViewer,
                                     selectionmodel=self.selectionmodel,
                                     stream='primary', field=field,
                                     bindings=[('sigTimeChangeFinished', self.indexChanged),
                                               (self.calibrationsettings.sigGeometryChanged, 'setGeometry')],
                                     geometry=self.getAI)
        self.comparemultiview = QLabel("COMING SOON!")  # SAXSMultiViewerPlugin(self.catalogModel, self.selectionmodel)

        # Setup correlation views
        self.correlationView = TabView(self.catalogModel, widgetcls=SAXSReductionViewer,
                                       selectionmodel=self.selectionmodel,
                                       stream='primary', field=field)
        self.twoTimeProcessor = TwoTimeParameterTree(processor=self.processTwoTime)
        self.twoTimeToolBar = XPCSToolBar(headermodel=self.catalogModel,
                                          selectionmodel=self.selectionmodel,
                                          view=self.correlationView.currentWidget,
                                          workflow=self.roiworkflow,
                                          index=0)
        self.oneTimeProcessor = OneTimeParameterTree(processor=self.processOneTime)
        self.oneTimeToolBar = XPCSToolBar(view=self.correlationView.currentWidget,
                                          workflow=self.roiworkflow,
                                          index=0)

        # Setup toolbars
        self.rawtoolbar = SAXSToolbarRaw(self.catalogModel, self.selectionmodel)
        self.masktoolbar = SAXSToolbarMask(self.catalogModel, self.selectionmodel)
        self.reducetoolbar = SAXSToolbarReduce(self.catalogModel, self.selectionmodel,
                                               view=self.reducetabview.currentWidget, workflow=self.reduceworkflow)
        self.reducetabview.kwargs['toolbar'] = self.reducetoolbar
        self.reducetoolbar.sigDeviceChanged.connect(self.deviceChanged)

        # Setup calibration widgets
        self.calibrationsettings.setModels(self.catalogModel, self.calibrationtabview.selectionmodel)
        self.calibrationpanel = CalibrationPanel(self.catalogModel, self.calibrationtabview.selectionmodel)
        self.calibrationpanel.sigDoCalibrateWorkflow.connect(self.doCalibrateWorkflow)
        self.calibrationsettings.sigGeometryChanged.connect(self.doSimulateWorkflow)

        # Setup masking widgets
        self.maskeditor = WorkflowEditor(self.maskingworkflow)
        self.maskeditor.sigWorkflowChanged.connect(self.doMaskingWorkflow)

        # Setup reduction widgets
        self.displayeditor = WorkflowEditor(self.displayworkflow)
        self.reduceeditor = WorkflowEditor(self.reduceworkflow)
        self.reduceplot = ResultsWidget(self.derivedDataModel)
        self.reducetoolbar.sigDoWorkflow.connect(self.doReduceWorkflow)
        self.reduceeditor.sigWorkflowChanged.connect(self.doReduceWorkflow)
        self.displayeditor.sigWorkflowChanged.connect(self.doDisplayWorkflow)
        self.reducetabview.currentChanged.connect(self.catalogChanged)

        # Setup correlation widgets
        self.correlationResults = ResultsWidget(self.derivedDataModel)

        self.stages = {
            'Calibrate': GUILayout(self.calibrationtabview,
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
                '2-Time Correlation': GUILayout(self.correlationView,
                                                top=self.twoTimeToolBar,
                                                rightbottom=self.twoTimeProcessor,
                                                bottom=self.correlationResults),
                '1-Time Correlation': GUILayout(self.correlationView,
                                                top=self.oneTimeToolBar,
                                                rightbottom=self.oneTimeProcessor,
                                                bottom=self.correlationResults)
            }
        }

        super(SAXSPlugin, self).__init__()

        # Start visualizations
        self.displayworkflow.visualize(self.reduceplot, imageview=lambda: self.reducetabview.currentWidget(),
                                       toolbar=self.reducetoolbar)

    def getAI(self):
        """ Convenience method to get current field's AI """
        device = self.reducetoolbar.detectorcombobox.currentText()
        ai = self.calibrationsettings.AI(device)
        return ai

    def indexChanged(self):
        if not self.reduceplot.toolbar.multiplot.isChecked():
            self.doReduceWorkflow()

    def catalogChanged(self):
        # TODO: both catalogChanged and deviceChanged will fire, redundantly, when the first image is opened
        self.doReduceWorkflow()
        self.doDisplayWorkflow()

    def deviceChanged(self, device_name):
        self.doReduceWorkflow()
        self.doDisplayWorkflow()

    def currentCatalog(self):
        return self.catalogModel.itemFromIndex(self.selectionmodel.currentIndex()).data(Qt.UserRole)

    def schema(self):
        saxs_schema = {
            "techniques": [
                {
                    "technique": "scattering",
                    "configuration": {
                        "geometry": "transmission",
                        "detector_model": "fastccd",
                    },
                    "data_mapping": {
                        # "incoming_energy": [
                        #    "baseline",
                        #    "E"
                        # ]
                        "data_image": [
                            "primary",
                            "fccd_image"
                        ],
                        "dark_image": [
                            "dark",
                            "fccd_image"
                        ]
                    },
                    "version": 0
                },
            ]}

        return saxs_schema

    def appendCatalog(self, catalog: BlueskyRun, **kwargs):
        catalog.metadata.update(self.schema())

        displayName = ""
        if 'sample_name' in catalog.metadata['start']:
            displayName = catalog.metadata['start']['sample_name']
        elif 'scan_id' in catalog.metadata['start']:
            displayName = f"Scan: {catalog.metadata['start']['scan_id']}"
        else:
            displayName = f"UID: {catalog.metadata['start']['uid']}"

        ensemble = Ensemble(catalogs=[catalog])
        item = CheckableItem(displayName)
        item.setData(displayName, Qt.DisplayRole)
        item.setData(ensemble, Qt.UserRole)
        self.catalogModel.appendRow(item)
        self.catalogModel.dataChanged.emit(item.index(), item.index())

    def checkDataShape(self, data):
        """Checks the shape of the data and gets the first frame if able to."""
        if data.shape[0] > 1:
            msg.notifyMessage("Looks like you did not open a single data frame. "
                              "Automated calibration only works with single frame data.")
            return None
        else:
            return data[0]

    @threads.method()
    def doCalibrateWorkflow(self, workflow: Workflow):
        data = self.calibrationtabview.currentWidget().image
        data = self.checkDataShape(data)
        if data is None: return
        device = self.rawtoolbar.detectorcombobox.currentText()
        ai = self.calibrationsettings.AI(device)
        # ai.detector = detectors.Pilatus2M()
        calibrant = self.calibrationpanel.parameter['Calibrant Material']

        def setAI(result):
            self.calibrationsettings.setAI(result['ai'].value, device)
            self.doMaskingWorkflow()

        workflow.execute(None, data=data, ai=ai, calibrant=calibrant, callback_slot=setAI, threadkey='calibrate')

    @threads.method()
    def doSimulateWorkflow(self, *_):
        # TEMPORARY HACK for demonstration
        # if self.reducetabview.currentWidget():
        #     threads.invoke_in_main_thread(self.reducetabview.currentWidget().setTransform)

        if not self.calibrationtabview.currentWidget(): return
        data = self.calibrationtabview.currentWidget().image
        data = self.checkDataShape(data)
        if data is None: return
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
            data = self.masktabview.currentWidget().image
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
        data = currentwidget.image
        data = [data[currentwidget.timeIndex(currentwidget.timeline)[0]]]
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
        return
        if not self.reducetabview.currentWidget(): return
        multimode = self.reducetoolbar.multiplot.isChecked()
        currentItem = self.catalogModel.itemFromIndex(self.selectionmodel.currentIndex())
        # FIXME -- hardcoded stream
        stream = "primary"
        data = currentItem.data(Qt.UserRole)
        field = self.reducetoolbar.detectorcombobox.currentText()
        if not field: return
        eventStream = getattr(currentItem.data(Qt.UserRole), stream).to_dask()[
            self.reducetoolbar.detectorcombobox.currentText()]
        if eventStream.ndim > 3:
            eventStream = eventStream[0]
        data = MetaXArray(eventStream)
        if not multimode:
            currentwidget = self.reducetabview.currentWidget()
            data = [data[currentwidget.timeIndex(currentwidget.timeLine)[0]]]
        device = self.reducetoolbar.detectorcombobox.currentText()
        ai = self.calibrationsettings.AI(device)
        if not ai: return
        ai = [ai] * len(data)
        mask = [self.maskingworkflow.lastresult[0]['mask'].value if self.maskingworkflow.lastresult else None] * len(
            data)

        def showReduce(*results):
            # FIXME -- Better way to get the hints from the results
            parentItem = CheckableItem("Scattering Reduction")
            for result in results:
                hints = next(iter(result.items()))[-1].parent.hints
                for hint in hints:
                    item = CheckableItem(hint.name)
                    item.setData(hint, Qt.UserRole)
                    parentItem.appendRow(item)
            self.derivedDataModel.appendRow(parentItem)

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
        pluginmaskclass = pluginmanager.get_plugin_by_name('Polygon Mask', 'ProcessingPlugin')
        for process in workflow.processes:
            if isinstance(process, pluginmaskclass):
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
        self.process(self.oneTimeProcessor, self.correlationView.currentWidget(),
                     finished_slot=self.updateDerivedDataModel)

    def processTwoTime(self):
        self.process(self.twoTimeProcessor, self.correlationView.currentWidget(),
                     finished_slot=self.updateDerivedDataModel)

    def process(self, processor: CorrelationParameterTree, widget, **kwargs):
        if processor:
            roiFuture = self.roiworkflow.execute(data=self.correlationView.currentWidget().image[0],
                                                 image=self.correlationView.currentWidget().imageItem)  # Pass in single frame for data shape
            roiResult = roiFuture.result()
            label = roiResult[-1]["roi"]
            if label is None:
                msg.notifyMessage("Please define an ROI using the toolbar before running correlation.")
                return

            workflow = processor.workflow
            # FIXME -- don't grab first match
            technique = \
                [technique for technique in self.schema()['techniques'] if technique['technique'] == 'scattering'][0]
            stream, field = technique['data_mapping']['data_image']
            # TODO: the compute() takes a long time..., do we need to do this here? If so, show a progress bar...
            # Trim the data frames
            catalog = self.currentCatalog()
            data = [getattr(catalog, stream).to_dask()[field][0].where(
                DataArray(label, dims=["dim_1", "dim_2"]), drop=True).compute()]
            # Trim the dark images
            msg.notifyMessage("Skipping dark correction...")
            darks = [None] * len(data)
            dark_stream, dark_field = technique['data_mapping']['dark_image']
            if stream in catalog:
                darks = [getattr(catalog, dark_stream).to_dask()[dark_field][0].where(
                    DataArray(label, dims=["dim_1", "dim_2"]), drop=True).compute()]
            else:
                msg.notifyMessage(f"No dark stream named \"{dark_stream}\" for current catalog. No dark correction.")
            label = label.compress(np.any(label, axis=0), axis=1).compress(np.any(label, axis=1), axis=0)
            labels = [label] * len(data)  # TODO: update for multiple ROIs
            numLevels = [1] * len(data)

            numBufs = []
            for i in range(len(data)):
                shape = data[i].shape[0]
                # multi_tau_corr requires num_bufs to be even
                if shape % 2:
                    shape += 1
                numBufs.append(shape)

            if kwargs.get('finished_slot'):
                finishedSlot = kwargs['finished_slot']
            else:
                finishedSlot = self.updateDerivedDataModel

            # workflow_pickle = pickle.dumps(workflow)
            workflow.execute_all(None,
                                 # data=data,
                                 images=data,
                                 darks=darks,
                                 labels=labels,
                                 finished_slot=partial(finishedSlot,
                                                       workflow=workflow))
                                                       # workflow_pickle=workflow_pickle))

    def updateDerivedDataModel(self, workflow, **kwargs):
        # TODO: update to store "Ensembles"
        # Ensemble contains Catalogs, contains data (g2, 2-time, etc.)
        parentItem = CheckableItem(workflow.name)
        for hint in workflow.hints:
            item = CheckableItem(hint.name)
            item.setData(hint, Qt.UserRole)
            item.setCheckable(True)
            parentItem.appendRow(item)
        self.derivedDataModel.appendRow(parentItem)


