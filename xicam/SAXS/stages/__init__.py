from functools import partial
from typing import Dict, List

import numpy as np
from databroker.core import BlueskyRun
from databroker.in_memory import BlueskyInMemoryCatalog
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QDialog, QListWidget, QHBoxLayout, QPushButton, QDialogButtonBox, \
    QVBoxLayout
from xicam.SAXS.workflows.roi import ROIWorkflow
from xicam.core import threads

from xicam.core.execution.workflow import ingest_result_set, project_intents
from xicam.core.intents import ROIIntent
from xicam.core.threads import invoke_in_main_thread
from xicam.gui.actions import Action
from xicam.gui.canvases import XicamIntentCanvas
from xicam.gui.models.treemodel import EnsembleModel
from xicam.gui.plugins.ensembleguiplugin import EnsembleGUIPlugin
from xicam.gui.widgets import PreviewWidget
from xicam.gui.widgets.linearworkfloweditor import WorkflowEditor
from xicam.plugins import GUILayout, manager as plugin_manager

from xicam.SAXS.calibration.workflows import SimulateWorkflow, CalibrationWorkflow
from xicam.SAXS.intents import SAXSImageIntent, GISAXSImageIntent
from xicam.SAXS.masking.workflows import MaskingWorkflow
from xicam.SAXS.operations.workflows import DisplayWorkflow, ReduceWorkflow
from xicam.SAXS.projectors.edf import project_NXsas
from xicam.SAXS.projectors.nxcansas import project_nxcanSAS
from xicam.SAXS.widgets.SAXSViewerPlugin import QLabel
from xicam.SAXS.workflows.xpcs import OneTime, TwoTime


# FIXME: the old way used TabWidget.currentWidget with XPCSToolBar...
# - previous: view was a tab view with the SAXSReductionViewer mixin as its widget
# - how can we adapt this to StackedCanvasView / CanvasView?
# # SAXS GUI Plugin mixin can use shared components
# class SAXSGUIPlugin(CorrelationGUIPlugin, SAXSReductionGUIPlugin)


class BaseSAXSGUIPlugin(EnsembleGUIPlugin):
    name = "SAXS"
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
        self.roiworkflow = ROIWorkflow()
        self.simulateworkflow = SimulateWorkflow()
        self.displayworkflow = DisplayWorkflow()
        self.reduceworkflow = ReduceWorkflow()

    def get_active_images(self, _):
        intent_indexes = [self.intents_model.index(row, 0) for row in range(self.intents_model.rowCount())]
        intents = {index: index.internalPointer()
                   for index in intent_indexes}
        image_indexes = list(filter(lambda index: isinstance(intents[index], SAXSImageIntent), intents.keys()))

        # FIXME: handle multiple images
        if len(image_indexes) > 1:
            image_names = [img.parent().data(Qt.DisplayRole) for img in image_indexes]
            raise ValueError("Running multiple images in this workflow is currently unsupported.")
        elif len(image_indexes) == 0:
            raise ValueError("No images are selected; cannot run this workflow.")

        image_index = image_indexes[0]
        canvas = self.intents_model.data(image_index, self.intents_model.canvas_role)
        # Test with time-series
        kwargs = {'images': np.squeeze(intents[image_index].image),
                  'image_item': canvas.canvas_widget.imageItem,
                  'geometry': intents[image_index].geometry}

        if 'darks' in intents[image_index].kwargs:
            kwargs['darks'] = np.squeeze(intents[image_index].kwargs['darks'])

        # Provide incidence angle and transmission mode based on SAXS v. GISAXS image intent type
        # TODO: if we support multiple image_indexes, will need to handle appropriately
        if isinstance(intents[image_index], GISAXSImageIntent):
            kwargs['transmission_mode'] = 'reflection'
            kwargs['incidence_angle'] = image_index.internalPointer().incidence_angle

        # Return the visualized (checked) rois as well
        roi_intents = list(filter(lambda intent: isinstance(intent, ROIIntent), intents.values()))
        rois = list(map(lambda intent: intent.roi, roi_intents))

        kwargs['rois'] = rois
        return kwargs


class ReduceGUIPlugin(BaseSAXSGUIPlugin):
    name = "Reduce"

    def __init__(self):
        super(ReduceGUIPlugin, self).__init__()

        self.reduce_panel = WorkflowEditor(self.reduceworkflow,
                                           kwargs_callable=self.begin_reduce,
                                           wavelength_override=0.124e-9,
                                           callback_slot=self.append_reduced)

        self.mask_panel = WorkflowEditor(self.maskingworkflow)
        self.display_panel = WorkflowEditor(self.displayworkflow)

        self.reduce_layout = GUILayout(self.canvases_view,
                                       right=self.ensemble_view,
                                       rightbottom=self.reduce_panel)
        stages = {'Reduce': self.reduce_layout}

        self.stages.update(**stages)

    def begin_masking(self, _, **kwargs):
        results = self.maskingworkflow.execute_synchronous(**kwargs)
        return list(results)[-1]

    def begin_roi(self, _, **kwargs):
        results = self.roiworkflow.execute_synchronous(**kwargs)
        return list(results)[-1]

    def begin_reduce(self, _):
        # # get catalogs from active ensemble
        # active_ensemble = self.ensemble_model.activeEnsemble
        # if not active_ensemble:
        #     raise RuntimeError("Unable to reduce since there is no data currently loaded. "
        #                        "Try opening data from the data browser on the left, "
        #                        "then retry running the reduction workflow.")
        #
        # # [] handles case where there is an active ensemble but no catalogs under it
        # active_catalogs = self.ensemble_model.catalogs() or []
        #
        # if not active_catalogs:
        #     raise RuntimeError("There are no catalogs in the active ensemble "
        #                        f'"{active_ensemble.data(Qt.DisplayRole)}". '
        #                        "Unable to reduce.")
        #
        # class ReduceDialog(QDialog):
        #     """Dialog for calibrating images.
        #
        #     User can select from a list of catalogs (pulled from the active ensemble),
        #     preview, and calibrate the image data.
        #     """
        #     def __init__(self, catalogs: List[BlueskyRun], parent=None, window_flags=Qt.WindowFlags()):
        #         super(ReduceDialog, self).__init__(parent, window_flags)
        #
        #         self.preview_widget = PreviewWidget()
        #
        #         self._catalogs = catalogs
        #
        #         self.catalog_selector = QListWidget()
        #         self.catalog_selector.addItems(map(lambda catalog: catalog.name, self._catalogs))
        #         self.catalog_selector.currentRowChanged.connect(self._update_preview)
        #
        #         calibrate_button = QPushButton("&Reduce")
        #         calibrate_button.setDefault(True)
        #
        #         self.buttons = QDialogButtonBox(Qt.Horizontal)
        #         # Add calibration button that accepts the dialog (closes with 1 status)
        #         self.buttons.addButton(calibrate_button, QDialogButtonBox.AcceptRole)
        #         # Add a cancel button that will reject the dialog (closes with 0 status)
        #         self.buttons.addButton(QDialogButtonBox.Cancel)
        #
        #         self.buttons.rejected.connect(self.reject)
        #         self.buttons.accepted.connect(self.accept)
        #
        #         layout = QHBoxLayout()
        #         layout.addWidget(self.catalog_selector)
        #         layout.addWidget(self.preview_widget)
        #
        #         outer_layout = QVBoxLayout()
        #         outer_layout.addLayout(layout)
        #         outer_layout.addWidget(self.buttons)
        #         self.setLayout(outer_layout)
        #
        #     def _update_preview(self, row: int):
        #         self.preview_widget.preview_catalog(self._catalogs[row])
        #
        #     def get_catalog(self):
        #         return self._catalogs[self.catalog_selector.currentRow()]
        #
        # if not active_catalogs:
        #     raise RuntimeError("There are no catalogs in the active ensemble "
        #                        f'"{active_ensemble.data(Qt.DisplayRole)}". '
        #                        "Unable to calibrate.")
        #
        # dialog = ReduceDialog(active_catalogs)
        # accepted = dialog.exec_()
        #
        # # Only calibrate if the dialog was accepted via the calibrate button
        # if not accepted == QDialog.Accepted:
        #     raise ValueError('Cancelled by user.')
        #
        # catalog = dialog.get_catalog()
        #
        # # TODO: better user feedback that there are no catalogs? (is that possible?)
        # if not catalog:
        #     raise ValueError('No catalog selected.')
        #
        # # find the saxsimageintent in this catalog
        # intents = self.ensemble_model.intents(catalog)
        #
        # image_intent = next(iter(filter(lambda intent: isinstance(intent, SAXSImageIntent), intents)))
        # data = image_intent.image
        #
        # kwargs = {"data": data}
        #
        # geometry = getattr(image_intent, 'geometry', None)
        # if geometry:
        #     kwargs['azimuthal_integrator'] = geometry
        #
        # masking_kwargs = self.begin_masking(None, **kwargs)
        #
        # kwargs.update(masking_kwargs)

        kwargs = self.get_active_images(None)
        kwargs['data'] = kwargs['images']
        kwargs['azimuthal_integrator'] = kwargs.get('geometry', None)

        masking_kwargs = self.begin_masking(None, **kwargs)
        kwargs.update(masking_kwargs)
        roi_kwargs = self.begin_roi(None, **kwargs)
        kwargs.update(roi_kwargs)

        kwargs['mask'] = kwargs['roi_mask']

        return kwargs

    def append_reduced(self, *results):
        document = list(ingest_result_set(self.reduceworkflow, results))
        # TODO: do we want to keep in memory catalog or write to attached databroker?
        # FIXME: use better bluesky_live design instead of upserting directly
        catalog = BlueskyInMemoryCatalog()
        catalog.upsert(document[0][1], document[-1][1], partial(iter, document), [], {})
        self.appendCatalog(catalog[-1])


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
        stages = {'Calibrate': self.calibrate_layout}

        self.stages.update(**stages)

    def begin_calibrate(self, _):
        # # get catalogs from active ensemble
        # active_ensemble = self.ensemble_model.activeEnsemble
        # if not active_ensemble:
        #     raise RuntimeError("Unable to calibrate since there is no data currently loaded. "
        #                        "Try opening data from the data browser on the left, "
        #                        "then retry running the calibration workflow.")
        #
        # # [] handles case where there is an active ensemble but no catalogs under it
        # active_catalogs = self.ensemble_model.catalogs() or []
        #
        # class CalibrationDialog(QDialog):
        #     """Dialog for calibrating images.
        #
        #     User can select from a list of catalogs (pulled from the active ensemble),
        #     preview, and calibrate the image data.
        #     """
        #     def __init__(self, catalogs: List[BlueskyRun], parent=None, window_flags=Qt.WindowFlags()):
        #         super(CalibrationDialog, self).__init__(parent, window_flags)
        #
        #         self.preview_widget = PreviewWidget()
        #
        #         self._catalogs = catalogs
        #
        #         self.catalog_selector = QListWidget()
        #         self.catalog_selector.addItems(map(lambda catalog: catalog.name, self._catalogs))
        #         self.catalog_selector.currentRowChanged.connect(self._update_preview)
        #
        #         calibrate_button = QPushButton("&Calibrate")
        #         calibrate_button.setDefault(True)
        #
        #         self.buttons = QDialogButtonBox(Qt.Horizontal)
        #         # Add calibration button that accepts the dialog (closes with 1 status)
        #         self.buttons.addButton(calibrate_button, QDialogButtonBox.AcceptRole)
        #         # Add a cancel button that will reject the dialog (closes with 0 status)
        #         self.buttons.addButton(QDialogButtonBox.Cancel)
        #
        #         self.buttons.rejected.connect(self.reject)
        #         self.buttons.accepted.connect(self.accept)
        #
        #         layout = QHBoxLayout()
        #         layout.addWidget(self.catalog_selector)
        #         layout.addWidget(self.preview_widget)
        #
        #         outer_layout = QVBoxLayout()
        #         outer_layout.addLayout(layout)
        #         outer_layout.addWidget(self.buttons)
        #         self.setLayout(outer_layout)
        #
        #     def _update_preview(self, row: int):
        #         self.preview_widget.preview_catalog(self._catalogs[row])
        #
        #     def get_catalog(self):
        #         return self._catalogs[self.catalog_selector.currentRow()]
        #
        # if not active_catalogs:
        #     raise RuntimeError("There are no catalogs in the active ensemble "
        #                        f'"{active_ensemble.data(Qt.DisplayRole)}". '
        #                        "Unable to calibrate.")
        #
        # dialog = CalibrationDialog(active_catalogs)
        # accepted = dialog.exec_()
        #
        # # Only calibrate if the dialog was accepted via the calibrate button
        # if not accepted == QDialog.Accepted:
        #     raise ValueError('Cancelled by user.')
        #
        # catalog = dialog.get_catalog()
        #
        # # TODO: better user feedback that there are no catalogs? (is that possible?)
        # if not catalog:
        #     raise ValueError('No catalog selected.')
        #
        # # find the saxsimageintent in this catalog
        # intents = self.ensemble_model.intents(catalog)
        #
        # image_intent = next(iter(filter(lambda intent: isinstance(intent, SAXSImageIntent), intents)))
        # data = image_intent.image

        kwargs = self.get_active_images(None)
        kwargs['data'] = kwargs['images']
        kwargs['azimuthal_integrator'] = kwargs.get('geometry', None)

        return kwargs

    def set_calibration(self, results):
        # TODO: confirmation dialog of calibration (or dialog of error)
        print(results)
        ai = results['azimuthal_integrator']

        # Find all intents within active ensemble, and set their geometry
        saxs_image_intents = [intent
                              for intent in
                              self.ensemble_model.intents(self.ensemble_model.activeEnsemble)
                              if isinstance(intent, SAXSImageIntent)]

        def _set_geometry(intent):
            intent.geometry = ai

        _ = list(map(_set_geometry, saxs_image_intents))

        calibration_settings = plugin_manager.get_plugin_by_name('xicam.SAXS.calibration', 'SettingsPlugin')
        device_names = list(map(lambda intent: intent.device_name, saxs_image_intents))

        for device_name in device_names:
            if device_name:
                calibration_settings.setAI(ai, device_name)

        # drop all canvases and refresh
        invoke_in_main_thread(self.canvases_view.refresh)


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
        stages = {"Correlation": GUILayout(**self.gui_layout_template)}
        self.stages.update(stages)

        self._roi_added = False

    def workflow_finished(self, *results):
        document = list(ingest_result_set(self.workflow, results))
        # TODO: do we want to keep in memory catalog or write to attached databroker?
        # FIXME: use better bluesky_live design instead of upserting directly
        catalog = BlueskyInMemoryCatalog()
        catalog.upsert(document[0][1], document[-1][1], partial(iter, document), [], {})
        self.appendCatalog(catalog[-1])

    def process_action(self, action: Action, canvas: XicamIntentCanvas):
        if not action.isAccepted():
            # Create ROI Intent adjacent to visualized intent
            roi_intent = ROIIntent(name=str(action.roi), roi=action.roi, match_key=canvas._primary_intent.match_key)
            catalog = self.ensemble_model.tree.parent(canvas._primary_intent)
            self.ensemble_model.appendIntent(roi_intent, catalog)

            self.workflow.auto_connect_all()
            action.accept()
        super(CorrelationStage, self).process_action(action, canvas)
