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
        # FIXME: refactor separation of SAXS v. XPCS
        self._projectors.extend([project_NXsas, project_nxcanSAS, project_intents])

        self.maskingworkflow = MaskingWorkflow()
        self.simulateworkflow = SimulateWorkflow()
        self.displayworkflow = DisplayWorkflow()
        self.reduceworkflow = ReduceWorkflow()


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
                                          rightbottom=self.calibration_panel)
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
            raise RuntimeError("Unable to calibrate since there is no data currently loaded. "
                               "Try opening data from the data browser on the left, "
                               "then retry running the calibration workflow.")

        # [] handles case where there is an active ensemble but no catalogs under it
        active_catalogs = self.ensemble_model.catalogs_from_ensemble(active_ensemble) or []

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
            raise RuntimeError("There are no catalogs in the active ensemble "
                               f'"{active_ensemble.data(Qt.DisplayRole)}". '
                               "Unable to calibrate.")

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
#
class CompareGUIPlugin(BaseSAXSGUIPlugin):
    name = "Compare"

    def __init__(self):
        super(CompareGUIPlugin, self).__init__()

        self.comparemultiview = QLabel("...")

        stages = {'Compare': GUILayout(self.comparemultiview,
                                       right=self.ensemble_view)}
        self.stages.update(**stages)


class CorrelationStage(BaseSAXSGUIPlugin):
    """
    Xi-CAM stage for XPCS correlation viewing and analysis.

    Features:
    * Open supported files in the data browser on the left, a preview will be shown when single-clicking the file.
    * Open configured databrokers to access and load bluesky runs.
    * Interactive tree-like viewer on the right-hand widget, where you can check/uncheck items to visualize and run analysis on.
    * Define ROIs on an opened and checked image item using the toolbar above the center widget.
    * Configurable and runnable 1-Time and 2-Time workflows in the bottom right widget.
    """
    name = "Correlation"
    # TODO: This doesn't really need to be two separate stages...
    def __init__(self):
        super(CorrelationStage, self).__init__()

        workflows = {OneTime(): '1-Time Correlation', TwoTime(): '2-Time Correlation'}
        self.workflow = next(iter(workflows.keys()))
        self.workflow.auto_connect_all()

        # FIXME: modify WorkflowEditor.workflow setter to allow changing workflow, kwargs_callable, etc.
        self.workflow_editor = WorkflowEditor(self.workflow,
                                              kwargs_callable=self.get_active_images,
                                              callback_slot=self.workflow_finished,
                                              workflows=workflows)
        self.gui_layout_template["rightbottom"] = self.workflow_editor
        self.stages[self.name] = GUILayout(**self.gui_layout_template)

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

        # FIXME: handle multiple images
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
