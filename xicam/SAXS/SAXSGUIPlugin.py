from PyQt5.QtWidgets import QLabel
from databroker.core import BlueskyRun

from xicam.core.workspace import Ensemble

from xicam.SAXS.stages import BaseSAXSGUIPlugin, CorrelationStage
from xicam.gui.widgets.views import DataSelectorView, StackedCanvasView
from xicam.plugins import GUILayout

from xicam.XPCS.projectors.nexus import project_nxXPCS


class SAXSPlugin(CorrelationStage):
    name = "SAXS"
# from xicam.SAXS.stages import BaseSAXSGUIPlugin, CorrelationStage, CompareGUIPlugin
# from xicam.gui.widgets.views import DataSelectorView, StackedCanvasView
# from xicam.plugins import GUILayout


# class SAXSPlugin(GUIPlugin):
    # name = 'SAXS'
# class SAXSPlugin(CorrelationStage, CompareGUIPlugin):

    def __init__(self):
        super(SAXSPlugin, self).__init__()
        self.projector = project_nxXPCS

    def appendCatalog(self, catalog: BlueskyRun, **kwargs):
        # catalog.metadata.update(self.schema())
        ensemble = Ensemble()
        ensemble.append_catalog(catalog)
        self.ensemble_model.add_ensemble(ensemble, project_nxXPCS)

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
        calibrant = self.calibrationpanel.parameter['Calibrant Material']

        def setAI(result):
            self.calibrationsettings.setAI(result['azimuthal_integrator'], device)
            self.doMaskingWorkflow()

        workflow.execute(None, data=data, azimuthal_integrator=ai, calibrant=calibrant, callback_slot=setAI, threadkey='calibrate')

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
            outputwidget.setCalibrantImage(result['data'])

        self.simulateworkflow.execute(None, data=data, azimuthal_integrator=ai, calibrant=calibrant, callback_slot=showSimulatedCalibrant,
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
                    outputwidget.setMaskImage(result['mask'])
                else:
                    outputwidget.setMaskImage(None)
                self.doDisplayWorkflow()
                self.doReduceWorkflow()

            if not workflow: workflow = self.maskingworkflow
            workflow.execute(None, data=data, azimuthal_integrator=ai, callback_slot=showMask, threadkey='masking')

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
        mask = self.maskingworkflow.lastresult[0]['mask'] if self.maskingworkflow.lastresult else None
        outputwidget = currentwidget

        def showDisplay(*results):
            outputwidget.setResults(results)

        self.displayworkflow.execute(None, data=data, azimuthal_integrator=ai, mask=mask, callback_slot=showDisplay, threadkey='display')

    @threads.method()
    def doReduceWorkflow(self):
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
        mask = [self.maskingworkflow.lastresult[0]['mask'] if self.maskingworkflow.lastresult else None] * len(
            data)

        def showReduce(*results):
            pass
            # # FIXME -- Better way to get the intents from the results
            # parentItem = CheckableItem("Scattering Reduction")
            # for result in results:
            #     hints = next(iter(result.items()))[-1].parent.hints
            #     for hint in hints:
            #         item = CheckableItem(hint.name)
            #         item.setData(hint, Qt.UserRole)
            #         parentItem.appendRow(item)
            # self.ensembleModel.appendRow(parentItem)
        # FROM MASTER MERGE
        #def showReduce(workflow, *_):
            # FIXME -- Better way to get the hints from the results
            #parentItem = CheckableItem("Scattering Reduction")
            #hints = workflow.hints
            #for hint in hints:
                #item = CheckableItem(hint.name)
                #item.setData(hint, Qt.UserRole)
                #parentItem.appendRow(item)
            #self.derivedDataModel.appendRow(parentItem)

        self.reduceworkflow.execute_all(None,
                                        data=data,
                                        azimuthal_integrator=ai,
                                        mask=mask,
                                        callback_slot=partial(showReduce, self.reduceworkflow),
                                        threadkey='reduce')

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
        # FIXME: Restore polygon masking via Intents/Canavases
        return False
        # pluginmaskclass = pluginmanager.get_plugin_by_name('Polygon Mask', 'ProcessingPlugin')
        # for process in workflow.processes:
        #     if isinstance(process, pluginmaskclass):
        #         if process.polygon is None:
        #             self.startPolygonMasking(process)
        #             return True
        # return False

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
        process.polygon = np.array([list(handle['pos']) for handle in viewer.maskROI.handles])
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
        pass
        # # TODO: update to store "Ensembles"
        # # Ensemble contains Catalogs, contains data (g2, 2-time, etc.)
        # parentItem = CheckableItem(workflow.name)
        # for hint in workflow.hints:
        #     item = CheckableItem(hint.name)
        #     item.setData(hint, Qt.UserRole)
        #     item.setCheckable(True)
        #     parentItem.appendRow(item)
        # self.ensembleModel.appendRow(parentItem)


        # super(SAXSPlugin, self).appendCatalog(catalog, projector=project_nxXPCS)
>>>>>>> Stashed changes
