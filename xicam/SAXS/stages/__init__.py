from functools import partial
from typing import Dict, List

from databroker.core import BlueskyRun
from databroker.in_memory import BlueskyInMemoryCatalog
from qtpy.QtCore import QItemSelectionModel, Qt
from qtpy.QtGui import QStandardItemModel
from qtpy.QtWidgets import QDialog, QListView, QWidget, QListWidget, QHBoxLayout, QPushButton, QDialogButtonBox, \
    QVBoxLayout
import numpy as np

from xicam.SAXS.intents import SAXSImageIntent, GISAXSImageIntent
from xicam.SAXS.operations.synthetic import synthetic_image_series
from xicam.SAXS.projectors.edf import project_NXsas
from xicam.SAXS.projectors.nxcansas import project_nxcanSAS

from xicam.core import msg, threads
from xicam.core.data import MetaXArray
from xicam.core.execution import Workflow
from xicam.core.execution.workflow import ingest_result_set, project_intents
from xicam.core.intents import ROIIntent
from xicam.gui.canvases import XicamIntentCanvas
from xicam.gui.widgets import PreviewWidget
from xicam.gui.widgets.ROI import ROIOperation
from xicam.gui.widgets.tabview import TabView
from xicam.plugins import GUILayout, GUIPlugin, manager as pluginmanager, OperationPlugin
from xicam.gui.models import IntentsModel, EnsembleModel
from xicam.gui.widgets.linearworkfloweditor import WorkflowEditor
from xicam.gui.widgets.views import StackedCanvasView, DataSelectorView

from xicam.SAXS.calibration.workflows import SimulateWorkflow, FourierCalibrationWorkflow, CalibrationWorkflow
from xicam.SAXS.masking.workflows import MaskingWorkflow
from xicam.SAXS.operations.workflows import DisplayWorkflow, ReduceWorkflow
from xicam.SAXS.widgets.parametertrees import CorrelationParameterTree, TwoTimeParameterTree, OneTimeParameterTree
from xicam.SAXS.widgets.SAXSViewerPlugin import SAXSViewerPluginBase, QDockWidget, QLabel
from xicam.SAXS.widgets.XPCSToolbar import XPCSToolBar
from xicam.SAXS.workflows.roi import ROIWorkflow
from xicam.SAXS.workflows.xpcs import OneTime, TwoTime

# need to be late imports?
from xicam.SAXS.calibration import CalibrationPanel
from xicam.SAXS.widgets.SAXSViewerPlugin import SAXSCalibrationViewer, SAXSMaskingViewer, SAXSReductionViewer, SAXSCompareViewer
from xicam.SAXS.widgets.SAXSToolbar import SAXSToolbarRaw, SAXSToolbarMask, SAXSToolbarReduce, SAXSToolbarBase
from xicam.SAXS.widgets.XPCSToolbar import XPCSToolBar


# FIXME: the old way used TabWidget.currentWidget with XPCSToolBar...
# - previous: view was a tab view with the SAXSReductionViewer mixin as its widget
# - how can we adapt this to StackedCanvasView / CanvasView?


# # SAXS GUI Plugin mixin can use shared components
# class SAXSGUIPlugin(CorrelationGUIPlugin, SAXSReductionGUIPlugin)

from xicam.gui.plugins.ensembleguiplugin import EnsembleGUIPlugin
from xicam.gui.actions import Action


class BaseSAXSGUIPlugin(EnsembleGUIPlugin):
    name="SAXS"
    # Re-implement abstract methods
    @property
    def exposedvars(self) -> Dict:
        pass

    def currentheader(self) -> Dict:
        pass

    def __init__(self):
        super(BaseSAXSGUIPlugin, self).__init__()

        # Add in appropriate projectors here
        # Make sure project_intents is last (since it is generic case)
        self._projectors.extend([project_NXsas, project_nxcanSAS, project_intents])

        # self.ensemble_model = EnsembleModel()
        # self.intents_model = IntentsModel()
        # self.intents_model.setSourceModel(self.ensemble_model)

        self.maskingworkflow = MaskingWorkflow()
        self.simulateworkflow = SimulateWorkflow()
        self.displayworkflow = DisplayWorkflow()
        self.reduceworkflow = ReduceWorkflow()

        self.toolbar = SAXSToolbarBase()
        # # FIXME: should workflow editor always require a workflow?
        # self.workflow_editor = WorkflowEditor(Workflow())
        #
        # self.field = "pilatus1M"
        #
        # self.ensemble_view = DataSelectorView()
        # self.ensemble_view.setModel(self.ensemble_model)
        # self.canvases_view = StackedCanvasView()
        # self.canvases_view.setModel(self.intents_model)


        # self.ensemble_model = EnsembleModel()
        # self.intents_model = IntentsModel()
        # self.intents_model.setSourceModel(self.ensemble_model)
        #
        # self.maskingworkflow = MaskingWorkflow()
        # self.simulateworkflow = SimulateWorkflow()
        # self.displayworkflow = DisplayWorkflow()
        # self.reduceworkflow = ReduceWorkflow()
        #
        # self.toolbar = SAXSToolbarBase()
        # # FIXME: should workflow editor always require a workflow?
        # self.workflow_editor = WorkflowEditor(Workflow())
        #
        # self.field = "pilatus1M"
        #
        # self.ensemble_view = DataSelectorView()
        # self.ensemble_view.setModel(self.ensemble_model)
        # def blah(c, p):
        #     print(f"\nselection changed:\n\tcurrent: {c.data(Qt.DisplayRole)}\n\tprevious: {p.data(Qt.DisplayRole)}")
        # self.ensemble_view.selectionModel().currentChanged.connect(blah)
        # self.canvases_view = StackedCanvasView()
        # self.canvases_view.setModel(self.intents_model)
        
        # super(BaseSAXSGUIPlugin, self).__init__()

#     def checkDataShape(self, data):
#         """Checks the shape of the data and gets the first frame if able to."""
#         if data.shape[0] > 1:
#             msg.notifyMessage("Looks like you did not open a single data frame. "
#                               "Automated calibration only works with single frame data.")
#             return None
#         else:
#             return data[0]
#
#     def checkPolygonsSet(self, workflow: Workflow):
#         """
#         Check for any unset polygonmask processes; start masking mode if found
#
#         Parameters
#         ----------
#         workflow: Workflow
#
#         Returns
#         -------
#         bool
#             True if unset polygonmask process is found
#
#         """
#         # FIXME: Restore polygon masking via Intents/Canavases
#         return False
#         # pluginmaskclass = pluginmanager.get_plugin_by_name('Polygon Mask', 'ProcessingPlugin')
#         # for process in workflow.processes:
#         #     if isinstance(process, pluginmaskclass):
#         #         if process.polygon is None:
#         #             self.startPolygonMasking(process)
#         #             return True
#         # return False
#
#     def indexChanged(self):
#         if not self.reduceplot.toolbar.multiplot.isChecked():
#             self.doReduceWorkflow()
#
#     def catalogChanged(self):
#         # TODO: both catalogChanged and deviceChanged will fire, redundantly, when the first image is opened
#         self.doReduceWorkflow()
#         self.doDisplayWorkflow()
#
#     def startPolygonMasking(self, process):
#         self.setEnabledOuterWidgets(False)
#
#         # Start drawing mode
#         viewer = self.masktabview.currentWidget()  # type: SAXSViewerPluginBase
#         viewer.imageItem.setDrawKernel(kernel=np.array([[0]]), mask=None, center=(0, 0), mode='add')
#         viewer.imageItem.drawMode = self.drawEvent
#         viewer.maskROI.clearPoints()
#
#         # Setup other signals
#         process.parameter.child('Finish Mask').sigActivated.connect(partial(self.finishMask, process))
#         process.parameter.child('Clear Selection').sigActivated.connect(self.clearMask)
#
#     def setEnabledOuterWidgets(self, enabled):
#         # Disable other widgets
#         mainwindow = self.masktabview.window()
#         for dockwidget in mainwindow.findChildren(QDockWidget):
#             dockwidget.setEnabled(enabled)
#         mainwindow.rightwidget.setEnabled(True)
#         self.maskeditor.workflowview.setEnabled(enabled)
#         self.masktabview.tabBar().setEnabled(enabled)
#         mainwindow.menuBar().setEnabled(enabled)
#         mainwindow.pluginmodewidget.setEnabled(enabled)
#
#     def clearMask(self):
#         viewer = self.masktabview.currentWidget()  # type: SAXSViewerPluginBase
#         viewer.maskROI.clearPoints()
#
#     def finishMask(self, process, sender):
#         viewer = self.masktabview.currentWidget()  # type: SAXSViewerPluginBase
#         process.polygon = np.array([list(handle['pos']) for handle in viewer.maskROI.handles])
#         self.setEnabledOuterWidgets(True)
#
#         # End drawing mode
#         viewer.imageItem.drawKernel = None
#         viewer.maskROI.clearPoints()
#         process.parameter.clearChildren()
#
#         # Redo workflow with polygon
#         self.doMaskingWorkflow()
#
#     def drawEvent(self, kernel, imgdata, mask, ss, ts, event):
#         viewer = self.masktabview.currentWidget()  # type: SAXSViewerPluginBase
#         viewer.maskROI.addFreeHandle(viewer.view.vb.mapSceneToView(event.scenePos()))
#         if len(viewer.maskROI.handles) > 1:
#             viewer.maskROI.addSegment(viewer.maskROI.handles[-2]['item'], viewer.maskROI.handles[-1]['item'])
#
#     def currentCatalog(self):
#         return self.catalogModel.itemFromIndex(self.selectionmodel.currentIndex()).data(Qt.UserRole)
#
#     def deviceChanged(self, device_name):
#         self.doReduceWorkflow()
#         self.doDisplayWorkflow()
#
#
#
#     @threads.method()
#     def doMaskingWorkflow(self, workflow=None):
#         if not self.masktabview.currentWidget(): return
#         if not self.checkPolygonsSet(self.maskingworkflow):
#             data = self.masktabview.currentWidget().image
#             device = self.masktoolbar.detectorcombobox.currentText()
#             ai = self.calibrationsettings.AI(device)
#             outputwidget = self.masktabview.currentWidget()
#
#             def showMask(result=None):
#                 if result:
#                     outputwidget.setMaskImage(result['mask'])
#                 else:
#                     outputwidget.setMaskImage(None)
#                 self.doDisplayWorkflow()
#                 self.doReduceWorkflow()
#
#             if not workflow: workflow = self.maskingworkflow
#             workflow.execute(None, data=data, azimuthal_integrator=ai, callback_slot=showMask, threadkey='masking')
#
#     # disabled
#     @threads.method()
#     def doDisplayWorkflow(self):
#         return
#         if not self.reducetabview.currentWidget(): return
#         currentwidget = self.reducetabview.currentWidget()
#         data = currentwidget.image
#         data = [data[currentwidget.timeIndex(currentwidget.timeline)[0]]]
#         device = self.reducetoolbar.detectorcombobox.currentText()
#         ai = self.calibrationsettings.AI(device)
#         if not ai: return
#         mask = self.maskingworkflow.lastresult[0]['mask'] if self.maskingworkflow.lastresult else None
#         outputwidget = currentwidget
#
#         def showDisplay(*results):
#             outputwidget.setResults(results)
#
#         self.displayworkflow.execute(None, data=data, azimuthal_integrator=ai, mask=mask, callback_slot=showDisplay,
#                                      threadkey='display')
#
#     @threads.method()
#     def doReduceWorkflow(self):
#         if not self.reducetabview.currentWidget(): return
#         multimode = self.reducetoolbar.multiplot.isChecked()
#         currentItem = self.catalogModel.itemFromIndex(self.selectionmodel.currentIndex())
#         # FIXME -- hardcoded stream
#         stream = "primary"
#         data = currentItem.data(Qt.UserRole)
#         field = self.reducetoolbar.detectorcombobox.currentText()
#         if not field: return
#         eventStream = getattr(currentItem.data(Qt.UserRole), stream).to_dask()[
#             self.reducetoolbar.detectorcombobox.currentText()]
#         if eventStream.ndim > 3:
#             eventStream = eventStream[0]
#         data = MetaXArray(eventStream)
#         if not multimode:
#             currentwidget = self.reducetabview.currentWidget()
#             data = [data[currentwidget.timeIndex(currentwidget.timeLine)[0]]]
#         device = self.reducetoolbar.detectorcombobox.currentText()
#         ai = self.calibrationsettings.AI(device)
#         if not ai: return
#         ai = [ai] * len(data)
#         mask = [self.maskingworkflow.lastresult[0]['mask'] if self.maskingworkflow.lastresult else None] * len(
#             data)
#
#         def showReduce(*results):
#             pass
#             # # FIXME -- Better way to get the intents from the results
#             # parentItem = CheckableItem("Scattering Reduction")
#             # for result in results:
#             #     hints = next(iter(result.items()))[-1].parent.hints
#             #     for hint in hints:
#             #         item = CheckableItem(hint.name)
#             #         item.setData(hint, Qt.UserRole)
#             #         parentItem.appendRow(item)
#             # self.ensembleModel.appendRow(parentItem)
#
#         # FROM MASTER MERGE
#         # def showReduce(workflow, *_):
#         # FIXME -- Better way to get the hints from the results
#         # parentItem = CheckableItem("Scattering Reduction")
#         # hints = workflow.hints
#         # for hint in hints:
#         # item = CheckableItem(hint.name)
#         # item.setData(hint, Qt.UserRole)
#         # parentItem.appendRow(item)
#         # self.derivedDataModel.appendRow(parentItem)
#
#         self.reduceworkflow.execute_all(None,
#                                         data=data,
#                                         azimuthal_integrator=ai,
#                                         mask=mask,
#                                         callback_slot=partial(showReduce, self.reduceworkflow),
#                                         threadkey='reduce')
#
#     def getAI(self):
#         """ Convenience method to get current field's AI """
#         device = self.reducetoolbar.detectorcombobox.currentText()
#         ai = self.calibrationsettings.AI(device)
#         return ai
#
#
# class CorrelationGUIPlugin(BaseSAXSGUIPlugin):
#     def __init__(self):
#         super(CorrelationGUIPlugin, self).__init__()
#
#         self.data_selector_view = DataSelectorView()
#         self.data_selector_view.setModel(self.ensemble_model)
#
#         self.canvases_view = StackedCanvasView()
#         self.canvases_view.setModel(self.intents_model)
#
#         self.roi_workflow = ROIWorkflow()
#         # THIS PROBABLY WONT WORK WITH THIS CANVAS VIEW
#         self.toolbar = XPCSToolBar(view=self.canvases_view.view, workflow=self.roi_workflow, index=0)
#
#         onetime_workflow = OneTime()
#         onetime_editor = WorkflowEditor(onetime_workflow)
#         # onetime_editor.sigRunWorkflow.disconnect(onetime_editor.run_workflow)
#         onetime_editor.sigRunWorkflow.connect(self.do_thing)
#
#         twotime_workflow = TwoTime()
#         twotime_editor = WorkflowEditor(twotime_workflow)
#         # twotime_editor.sigRunWorkflow.disconnect(twotime_editor.run_workflow)
#         twotime_editor.sigRunWorkflow.connect(self.do_thing)
#
#         self.stages['Correlate'] = {
#             "2-Time Correlation": GUILayout(center=self.canvases_view,
#                                             righttop=self.data_selector_view,
#                                             top=self.toolbar,
#                                             rightbottom=twotime_editor),
#             "1-Time Correlation": GUILayout(center=self.canvases_view,
#                                             righttop=self.data_selector_view,
#                                             top=self.toolbar,
#                                             rightbottom=onetime_editor)
#         }
#
#     def do_thing(self):
#         msg.notifyMessage("WORKFLOW RUNNING...")
#         # Grab the "current" image?
#         # How do we know what the current image is?
#         images = None
#         # Execute roi workflow
#         # Can we embed the roi-workflow in core / gui operations eventually?
#         # Execute the workflow editor workflow
#         roi_result = None
#         with msg.busyContext():
#             roi_future = self.roi_workflow.execute(data=None, image=None)
#             roi_result = roi_future
#         roi_result = roi_future.result()
#         label = roi_result[-1]["roi"]
#
# # if processor:
# #     roiFuture = self.roiworkflow.execute(data=self.correlationView.currentWidget().image[0],
# #                                          image=self.correlationView.currentWidget().imageItem)  # Pass in single frame for data shape
# #     roiResult = roiFuture.result()
# #     label = roiResult[-1]["roi"]
# #     if label is None:
# #         msg.notifyMessage("Please define an ROI using the toolbar before running correlation.")
# #         return
# #
# #     workflow = processor.workflow
# #     # FIXME -- don't grab first match
# #     technique = \
# #         [technique for technique in self.schema()['techniques'] if technique['technique'] == 'scattering'][0]
# #     stream, field = technique['data_mapping']['data_image']
# #     # TODO: the compute() takes a long time..., do we need to do this here? If so, show a progress bar...
# #     # Trim the data frames
# #     catalog = self.currentCatalog()
# #     data = [getattr(catalog, stream).to_dask()[field][0].where(
# #         DataArray(label, dims=["dim_1", "dim_2"]), drop=True).compute()]
# #     # Trim the dark images
# #     msg.notifyMessage("Skipping dark correction...")
# #     darks = [None] * len(data)
# #     dark_stream, dark_field = technique['data_mapping']['dark_image']
# #     if stream in catalog:
# #         darks = [getattr(catalog, dark_stream).to_dask()[dark_field][0].where(
# #             DataArray(label, dims=["dim_1", "dim_2"]), drop=True).compute()]
# #     else:
# #         msg.notifyMessage(f"No dark stream named \"{dark_stream}\" for current catalog. No dark correction.")
# #     label = label.compress(np.any(label, axis=0), axis=1).compress(np.any(label, axis=1), axis=0)
# #     labels = [label] * len(data)  # TODO: update for multiple ROIs
# #     numLevels = [1] * len(data)
# #
# #     numBufs = []
# #     for i in range(len(data)):
# #         shape = data[i].shape[0]
# #         # multi_tau_corr requires num_bufs to be even
# #         if shape % 2:
# #             shape += 1
# #         numBufs.append(shape)
# #
# #     if kwargs.get('finished_slot'):
# #         finishedSlot = kwargs['finished_slot']
# #     else:
# #         finishedSlot = self.updateDerivedDataModel
# #
# #     # workflow_pickle = pickle.dumps(workflow)
# #     workflow.execute_all(None,
# #                          # data=data,
# #                          images=data,
# #                          darks=darks,
# #                          labels=labels,
# #                          finished_slot=partial(finishedSlot,
# #                                                workflow=workflow))
# #                                                # workflow_pickle=workflow_pickle))
#
#
# class CalibrateGUIPlugin(BaseSAXSGUIPlugin):
#     name = "Calibrate"
#
#     def __init__(self):
#         super(CalibrateGUIPlugin, self).__init__()
#
#         self.calibrationsettings = pluginmanager.get_plugin_by_name('xicam.SAXS.calibration',
#                                                                     'SettingsPlugin')
#
#         self.calibrationtabview = TabView(self.catalogModel, widgetcls=SAXSCalibrationViewer,
#                                           stream='primary', field=self.field,
#                                           selectionmodel=self.selectionmodel,
#                                           bindings=[(self.calibrationsettings.sigGeometryChanged, 'setGeometry')],
#                                           geometry=self.getAI)
#
#         self.calibrationsettings.setModels(self.catalogModel, self.calibrationtabview.selectionmodel)
#         self.calibrationpanel = CalibrationPanel(self.catalogModel, self.calibrationtabview.selectionmodel)
#         self.calibrationpanel.sigDoCalibrateWorkflow.connect(self.doCalibrateWorkflow)
#         self.calibrationsettings.sigGeometryChanged.connect(self.doSimulateWorkflow)
#
#         stages = {'Calibrate': GUILayout(self.calibrationtabview,
#                                          right=self.calibrationsettings.widget,
#                                          rightbottom=self.calibrationpanel,
#                                          top=self.toolbar), }
#         self.stages.update(**stages)
class CalibrateGUIPlugin(BaseSAXSGUIPlugin):
    name = "Calibrate"

    def __init__(self):
        super(CalibrateGUIPlugin, self).__init__()

        self.calibration_workflow = CalibrationWorkflow()
        self.calibration_panel = WorkflowEditor(self.calibration_workflow,
                                                kwargs_callable=self.begin_calibrate,
                                                wavelength_override=0.124e-9,
                                                callback_slot=self.set_calibration)

        self.calibrate_layout = GUILayout(self.canvases_view,
                                          right=self.ensemble_view,
                                          rightbottom=self.calibration_panel,
                                          top=self.toolbar)
        # stages = {'Calibrate': GUILayout(self.calibration_view,
        #                                  right=self.calibrationsettings.widget,
        #                                  rightbottom=self.calibrationpanel,
        #                                  top=self.toolbar), }
        stages = {'Calibrate': self.calibrate_layout}

        self.stages.update(**stages)

    def begin_calibrate(self, _):
        # get catalogs from active ensemble
        active_ensemble = self.ensemble_model.active_ensemble
        if not active_ensemble:
            return

        active_catalogs = self.ensemble_model.catalogs_from_ensemble(active_ensemble)

        class CalibrationDialog(QDialog):
            """Dialog for calibrating images.

            User can select from a list of catalogs (pulled from the active ensemble),
            preview, and calibrate the image data.
            """
            def __init__(self, catalogs: List[BlueskyRun], parent=None, window_flags=Qt.WindowFlags()):
                super(CalibrationDialog, self).__init__(parent, window_flags)

                self.preview_widget = PreviewWidget()

                self._catalogs = catalogs

                self.catalog_selector = QListWidget()
                self.catalog_selector.addItems(map(lambda catalog: catalog.name, self._catalogs))
                self.catalog_selector.currentRowChanged.connect(self._update_preview)

                calibrate_button = QPushButton("&Calibrate")
                calibrate_button.setDefault(True)

                self.buttons = QDialogButtonBox(Qt.Horizontal)
                # Add calibration button that accepts the dialog (closes with 1 status)
                self.buttons.addButton(calibrate_button, QDialogButtonBox.AcceptRole)
                # Add a cancel button that will reject the dialog (closes with 0 status)
                self.buttons.addButton(QDialogButtonBox.Cancel)

                self.buttons.rejected.connect(self.reject)
                self.buttons.accepted.connect(self.accept)

                layout = QHBoxLayout()
                layout.addWidget(self.catalog_selector)
                layout.addWidget(self.preview_widget)

                outer_layout = QVBoxLayout()
                outer_layout.addLayout(layout)
                outer_layout.addWidget(self.buttons)
                self.setLayout(outer_layout)

            def _update_preview(self, row: int):
                self.preview_widget.preview_catalog(self._catalogs[row])

            def get_catalog(self):
                return self._catalogs[self.catalog_selector.currentRow()]

        if not active_catalogs:
            msg.logMessage("No catalogs in active ensemble found, cannot calibrate.", msg.WARNING)
            return

        dialog = CalibrationDialog(active_catalogs)
        accepted = dialog.exec_()

        # Only calibrate if the dialog was accepted via the calibrate button
        if not accepted == QDialog.Accepted:
            return

        catalog = dialog.get_catalog()

        # TODO: better user feedback that there are no catalogs? (is that possible?)
        if not catalog:
            return

        # find the saxsimageintent in this catalog
        intents = self.ensemble_model.intents_from_catalog(catalog)

        image_intent = next(iter(filter(lambda intent: isinstance(intent, SAXSImageIntent), intents)))
        data = image_intent.image
        return {"data": data}


    def set_calibration(self, results):
        # TODO: confirmation dialog of calibration (or dialog of error)
        print(results)
        ai = results['azimuthal_integrator']

        # Find all intents within active ensemble, and set their geometry
        saxs_image_intents = [intent
                              for intents in
                              self.ensemble_model.intents_from_ensemble(self.ensemble_model.active_ensemble).values()
                              for intent in intents
                              if isinstance(intent, SAXSImageIntent)]

        def _set_geometry(intent):
            intent.geometry = ai

        _ = list(map(_set_geometry, saxs_image_intents))

        # drop all canvases and refresh
        self.canvases_view.refresh()

#
#     @threads.method()
#     def doCalibrateWorkflow(self, workflow: Workflow):
#         data = self.calibrationtabview.currentWidget().image
#         data = self.checkDataShape(data)
#         if data is None: return
#         device = self.toolbar.detectorcombobox.currentText()
#         ai = self.calibrationsettings.AI(device)
#         calibrant = self.calibrationpanel.parameter['Calibrant Material']
#
#         def setAI(result):
#             self.calibrationsettings.setAI(result['azimuthal_integrator'], device)
#             self.doMaskingWorkflow()
#
#         workflow.execute(None, data=data, azimuthal_integrator=ai, calibrant=calibrant, callback_slot=setAI,
#                          threadkey='calibrate')
#
#     @threads.method()
#     def doSimulateWorkflow(self, *_):
#         # TEMPORARY HACK for demonstration
#         # if self.reducetabview.currentWidget():
#         #     threads.invoke_in_main_thread(self.reducetabview.currentWidget().setTransform)
#
#         if not self.calibrationtabview.currentWidget():
#             return
#         data = self.calibrationtabview.currentWidget().image
#         data = self.checkDataShape(data)
#         if data is None:
#             return
#         device = self.toolbar.detectorcombobox.currentText()
#         ai = self.calibrationsettings.AI(device)
#         if not ai:
#             return
#         calibrant = self.calibrationpanel.parameter['Calibrant Material']
#         outputwidget = self.calibrationtabview.currentWidget()
#
#         def showSimulatedCalibrant(result=None):
#             outputwidget.setCalibrantImage(result['data'])
#
#         self.simulateworkflow.execute(None, data=data, azimuthal_integrator=ai, calibrant=calibrant,
#                                       callback_slot=showSimulatedCalibrant,
#                                       threadkey='simulate')
#
#
class CompareGUIPlugin(BaseSAXSGUIPlugin):
    name = "Compare"

    def __init__(self):
        super(CompareGUIPlugin, self).__init__()

        self.comparemultiview = QLabel("...")

        stages = {'Compare': GUILayout(self.comparemultiview,
                                       top=self.toolbar,
                                       right=self.ensemble_view)}
        self.stages.update(**stages)
#
#
# class MaskGUIPlugin(BaseSAXSGUIPlugin):
#     name = "Mask"
#
#     def __init__(self):
#         super(MaskGUIPlugin, self).__init__()
#
#         self.toolbar = SAXSToolbarMask(self.catalogModel, self.selectionmodel)
#         self.workflow_editor.workflow = self.maskingworkflow
#         self.workflow_editor.sigWorkflowChanged.connect(self.doMaskingWorkflow)
#
#         self.masktabview = TabView(self.catalogModel, widgetcls=SAXSMaskingViewer, selectionmodel=self.selectionmodel,
#                                    stream='primary', field=self.field,
#                                    bindings=[('sigTimeChangeFinished', self.indexChanged),
#                                              (self.calibrationsettings.sigGeometryChanged, 'setGeometry')],
#                                    geometry=self.getAI)
#
#
#         stages = {'Mask': GUILayout(self.masktabview, right=self.workflow_editor, top=self.toolbar)}
#         self.stages.update(**stages)
#
#
# class ReduceGUIPlugin(BaseSAXSGUIPlugin):
#     name = "Reduce"
#
#     def __init__(self):
#         super(ReduceGUIPlugin, self).__init__()
#
#         self.toolbar = SAXSToolbarReduce(self.catalogModel, self.selectionmodel,
#                                                view=self.reducetabview.currentWidget, workflow=self.reduceworkflow)
#
#         self.toolbar = SAXSToolbarReduce(view=self.)
#
#
#         self.toolbar = SAXSToolbarReduce(self.catalogModel, self.selectionmodel,
#                                          view=self.reducetabview.currentWidget, workflow=self.reduceworkflow)
#         # self.comparetoolbar = SAXSToolbarCompare()
#         self.reducetabview.kwargs['toolbar'] = self.reducetoolbar
#         self.reducetoolbar.sigDeviceChanged.connect(self.deviceChanged)
#
#
#         self.reducetabview = TabView(catalogmodel=self.catalogModel, widgetcls=SAXSReductionViewer,
#                                      selectionmodel=self.selectionmodel,
#                                      stream='primary', field=self.field,
#                                      bindings=[('sigTimeChangeFinished', self.indexChanged),
#                                                (self.calibrationsettings.sigGeometryChanged, 'setGeometry')],
#                                      geometry=self.getAI)
#
#         self.displayeditor = WorkflowEditor(self.displayworkflow)
#         self.reduceeditor = WorkflowEditor(self.reduceworkflow)
#         self.reduceplot = QLabel('...')
#         self.reducetoolbar.sigDoWorkflow.connect(self.doReduceWorkflow)
#         self.reduceeditor.sigWorkflowChanged.connect(self.doReduceWorkflow)
#         self.displayeditor.sigWorkflowChanged.connect(self.doDisplayWorkflow)
#         self.reducetabview.currentChanged.connect(self.catalogChanged)
#
#
#
#         stages = {'Reduce': GUILayout(center=self.reducetabview,
#                                       bottom=self.reduceplot, right=self.reduceeditor, righttop=self.displayeditor,
#                                       top=self.toolbar),}
#
#         self.stages.update(**stages)


# class CorrelationStage(QWidget):
#     def __init__(self, model, parent=None, **layout_kwargs):
#
#         if layout_kwargs.pop("center", None) is not None:
#             msg.notifyMessage("CorrelationStage already provides a \"center\" widget.", msg.WARNING)
#
#         if layout_kwargs.pop("righttop", None) is not None:
#             msg.notifyMessage("CorerlationStage already provides a \"righttop\" widget.", msg.WARNING)
#
#         self.model = model
#         self.intents_model = IntentsModel()
#         self.intents_model.setSourceModel(self.model)
#
#         self.data_selector_view = DataSelectorView()
#         self.data_selector_view.setModel(model)
#
#         self.canvases_view = StackedCanvasView()
#         self.canvases_view.setModel(self.intents_model)
#
#         self.roi_workflow = ROIWorkflow()
#         # THIS PROBABLY WONT WORK WITH THIS CANVAS VIEW
#         self.toolbar = XPCSToolBar(view=self.canvases_view.view, workflow=self.roi_workflow, index=0)
#         # Tool bar mixin can be a view kwarg
#
#         # view_kwargs -> sequence of "str" (can't be types... needs to be serializable), need another registry?
#         # ImageCanvas.__init__(..., **view_kwargs)
#         # ImageCanvas.__new__(..., **view_kwargs):
#             # Build new view type with view_kwargs
#         # meta-programmable canvas
#
#         self.gui_layout = GUILayout(center=self.canvases_view,
#                                     righttop=self.data_selector_view,
#                                     top=self.toolbar,
#                                     **layout_kwargs)
#
#         super(CorrelationStage, self).__init__(parent=parent)
#
#     def do_thing(self):
#         msg.notifyMessage("WORKFLOW RUNNING...")
#         # Grab the "current" image?
#         # How do we know what the current image is?
#         images = None
#         # Execute roi workflow
#         # Can we embed the roi-workflow in core / gui operations eventually?
#         # Execute the workflow editor workflow
#         roi_result = None
#         with msg.busyContext():
#             roi_future = self.roi_workflow.execute(data=None, image=None)
#             roi_result = roi_future
#         roi_result = roi_future.result()
#         label = roi_result[-1]["roi"]


# if processor:
#     roiFuture = self.roiworkflow.execute(data=self.correlationView.currentWidget().image[0],
#                                          image=self.correlationView.currentWidget().imageItem)  # Pass in single frame for data shape
#     roiResult = roiFuture.result()
#     label = roiResult[-1]["roi"]
#     if label is None:
#         msg.notifyMessage("Please define an ROI using the toolbar before running correlation.")
#         return
#
#     workflow = processor.workflow
#     # FIXME -- don't grab first match
#     technique = \
#         [technique for technique in self.schema()['techniques'] if technique['technique'] == 'scattering'][0]
#     stream, field = technique['data_mapping']['data_image']
#     # TODO: the compute() takes a long time..., do we need to do this here? If so, show a progress bar...
#     # Trim the data frames
#     catalog = self.currentCatalog()
#     data = [getattr(catalog, stream).to_dask()[field][0].where(
#         DataArray(label, dims=["dim_1", "dim_2"]), drop=True).compute()]
#     # Trim the dark images
#     msg.notifyMessage("Skipping dark correction...")
#     darks = [None] * len(data)
#     dark_stream, dark_field = technique['data_mapping']['dark_image']
#     if stream in catalog:
#         darks = [getattr(catalog, dark_stream).to_dask()[dark_field][0].where(
#             DataArray(label, dims=["dim_1", "dim_2"]), drop=True).compute()]
#     else:
#         msg.notifyMessage(f"No dark stream named \"{dark_stream}\" for current catalog. No dark correction.")
#     label = label.compress(np.any(label, axis=0), axis=1).compress(np.any(label, axis=1), axis=0)
#     labels = [label] * len(data)  # TODO: update for multiple ROIs
#     numLevels = [1] * len(data)
#
#     numBufs = []
#     for i in range(len(data)):
#         shape = data[i].shape[0]
#         # multi_tau_corr requires num_bufs to be even
#         if shape % 2:
#             shape += 1
#         numBufs.append(shape)
#
#     if kwargs.get('finished_slot'):
#         finishedSlot = kwargs['finished_slot']
#     else:
#         finishedSlot = self.updateDerivedDataModel
#
#     # workflow_pickle = pickle.dumps(workflow)
#     workflow.execute_all(None,
#                          # data=data,
#                          images=data,
#                          darks=darks,
#                          labels=labels,
#                          finished_slot=partial(finishedSlot,
#                                                workflow=workflow))
#                                                # workflow_pickle=workflow_pickle))

class CorrelationStage(BaseSAXSGUIPlugin):
    name = "Correlation"
    # TODO: This doesn't really need to be two separate stages...
    def __init__(self):
        super(CorrelationStage, self).__init__()

        workflows = {OneTime(): '1-Time Correlation', TwoTime(): '2-Time Correlation'}
        self.workflow = next(iter(workflows.keys()))
        self.workflow.auto_connect_all()

        correlation_workflow_editor = WorkflowEditor(self.workflow,
                                                     kwargs_callable=self.get_active_images,
                                                     callback_slot=self.workflow_finished,
                                                     workflows=workflows)
        correlation_layout = GUILayout(center=self.canvases_view,
                                       right=self.ensemble_view,
                                       rightbottom=correlation_workflow_editor,
                                       top=self.toolbar)
        self.stages["Correlation"] = correlation_layout

        self._roi_added = False

    def workflow_finished(self, *results):
        document = list(ingest_result_set(self.workflow, results))
        # TODO: do we want to keep in memory catalog or write to attached databroker?
        # FIXME: use better bluesky_live design instead of upserting directly
        catalog = BlueskyInMemoryCatalog()
        catalog.upsert(document[0][1], document[-1][1], partial(iter, document), [], {})
        # project_intents(catalog)
        self.appendCatalog(catalog[-1])

    def get_active_images(self, workflow_editor: WorkflowEditor):
        self.workflow = workflow_editor.workflow
        intent_indexes = [self.intents_model.index(row, 0) for row in range(self.intents_model.rowCount())]
        intents = {self.intents_model.data(index, IntentsModel.index_role): self.intents_model.data(index,
                                                                                                    IntentsModel.intent_role)
                   for index in intent_indexes}
        # self.ensemble_model.intents_from_ensemble(self.ensemble_model.active_ensemble)
        image_indexes = list(filter(lambda index: isinstance(intents[index], SAXSImageIntent), intents.keys()))

        if len(image_indexes) > 1:
            ...
            raise ValueError('...')
        elif len(image_indexes) == 0:
            ...
            raise ValueError('...')

        image_index = image_indexes[0]
        canvas = self.canvases_view._canvas_manager.canvas_from_index(image_index)
        # Test with time-series
        kwargs = {'images': np.squeeze(intents[image_index].image),
                  'image_item': canvas.canvas_widget.imageItem,
                  'geometry': intents[image_index].geometry}

        # Disable diffusion coefficient op when no geometry provided
        # TODO: handling in the diffusion coefficient op itself is problematic, since it is an end node -
        #     what should be returned / how would the intents be visualized?
        if intents[image_index].geometry is None:
            diffusion_op = next(filter(lambda op: op.name == "Diffusion Coefficient", self.workflow.operations), None)
            if diffusion_op is not None:
                source_data = image_index.internalPointer()
                image_name = source_data.data(Qt.DisplayRole)
                image_catalog = source_data.parentItem.data(Qt.DisplayRole)
                image_ensemble = source_data.parentItem.parentItem.data(Qt.DisplayRole)
                msg.notifyMessage(
                    f"No valid geometry found for:"
                    f"\n\t{image_ensemble} -> {image_catalog} -> {image_name}.\""
                    f"\nDiffusion Coefficient operation has been disabled.",
                    title=f"No Geometry Found",
                    level=msg.WARNING)
                self.workflow.set_disabled(diffusion_op)

        # Provide incidence angle and transmission mode based on SAXS v. GISAXS image intent type
        # TODO: if we support multiple image_indexes, will need to handle appropriately
        if isinstance(intents[image_index], GISAXSImageIntent):
            kwargs['transmission_mode'] = 'reflection'
            kwargs['incidence_angle'] = image_index.data(EnsembleModel.object_role).incidence_angle

        # Return the visualized (checked) rois as well
        roi_intent_indexes = filter(lambda index: isinstance(intents[index], ROIIntent)
                                                  and index.data(Qt.CheckStateRole) == Qt.Checked,
                                    intents.keys())
        rois = list(map(lambda index: index.data(EnsembleModel.object_role).roi, roi_intent_indexes))

        kwargs['rois'] = rois
        return kwargs

    def process_action(self, action: Action, canvas: XicamIntentCanvas):
        if not action.isAccepted():
            # Create ROI Intent adjacent to visualized intent
            roi_intent = ROIIntent(name=str(action.roi), roi=action.roi, match_key=canvas._primary_intent.match_key)
            catalog = self.ensemble_model.catalog_from_intent(canvas._primary_intent)
            self.ensemble_model.append_to_catalog(catalog, roi_intent)

            self.workflow.auto_connect_all()
            action.accept()
        super(CorrelationStage, self).process_action(action, canvas)
