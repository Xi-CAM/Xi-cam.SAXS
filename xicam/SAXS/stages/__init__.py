from functools import partial
from typing import Dict

from databroker.core import BlueskyRun
from qtpy.QtCore import QItemSelectionModel, Qt
from qtpy.QtGui import QStandardItemModel
import numpy as np

from xicam.core import msg, threads
from xicam.core.data import MetaXArray
from xicam.core.execution import Workflow
from xicam.gui.widgets.tabview import TabView
from xicam.plugins import GUILayout, GUIPlugin, manager as pluginmanager
from xicam.gui.models import IntentsModel, EnsembleModel
from xicam.gui.widgets.linearworkfloweditor import WorkflowEditor
from xicam.gui.widgets.views import StackedCanvasView, DataSelectorView

from xicam.SAXS.calibration.workflows import SimulateWorkflow
from xicam.SAXS.masking.workflows import MaskingWorkflow
from xicam.SAXS.processing.workflows import DisplayWorkflow, ReduceWorkflow
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

class BaseSAXSGUIPlugin(GUIPlugin):
    # Re-implement abstract methods
    @property
    def exposedvars(self) -> Dict:
        pass

    def currentheader(self) -> Dict:
        pass

    def __init__(self):
        super(BaseSAXSGUIPlugin, self).__init__()

        self.ensemble_model = EnsembleModel()
        self.intents_model = IntentsModel()
        self.intents_model.setSourceModel(self.ensemble_model)

        self.maskingworkflow = MaskingWorkflow()
        self.simulateworkflow = SimulateWorkflow()
        self.displayworkflow = DisplayWorkflow()
        self.reduceworkflow = ReduceWorkflow()

        self.toolbar = SAXSToolbarBase()
        # FIXME: should workflow editor always require a workflow?
        self.workflow_editor = WorkflowEditor(Workflow())

        self.field = "pilatus1M"

        self.ensemble_view = DataSelectorView()
        self.ensemble_view.setModel(self.ensemble_model)
        self.canvases_view = StackedCanvasView()
        self.canvases_view.setModel(self.intents_model)
        
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
# class CompareGUIPlugin(BaseSAXSGUIPlugin):
#     name = "Compare"
#
#     def __init__(self):
#         super(CompareGUIPlugin, self).__init__()
#
#         self.comparemultiview = QLabel("...")
#
#         stages = {'Compare': GUILayout(self.comparemultiview, top=self.toolbar,
#                              right=QLabel('dataselectorview'))}
#         self.stages.update(**stages)
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
    # TODO: This doesn't really need to be two separate stages...
    def __init__(self):
        super(CorrelationStage, self).__init__()
        self.stages["Correlation"] = {}

        onetime_workflow_editor = WorkflowEditor(OneTime())
        onetime_layout = GUILayout(center=self.canvases_view,
                                   right=self.ensemble_view,
                                   rightbottom=onetime_workflow_editor,
                                   top=self.toolbar)
        self.stages["Correlation"]["1-Time"] = onetime_layout

        twotime_workflow_editor = WorkflowEditor(TwoTime())
        twotime_layout = GUILayout(center=self.canvases_view,
                                   right=self.ensemble_view,
                                   rightbottom=twotime_workflow_editor,
                                   top=self.toolbar)
        self.stages["Correlation"]["2-Time"] = twotime_layout




# class OneTimeCorrelationStage(BaseSAXSGUIPlugin):
#     name = "1-Time Correlation"
#     def __init__(self):
#         super(OneTimeCorrelationStage, self).__init__()

        # onetime_workflow = OneTime()
        # onetime_editor = WorkflowEditor(onetime_workflow)
        # onetime_editor.sigRunWorkflow.connect(self.do_thing)
        # onetime_editor.sigRunWorkflow.disconnect(onetime_editor.run_workflow)

