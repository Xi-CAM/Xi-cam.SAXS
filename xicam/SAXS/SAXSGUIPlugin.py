from PyQt5.QtWidgets import QLabel
from databroker.core import BlueskyRun

from xicam.core.workspace import Ensemble

from xicam.SAXS.stages import BaseSAXSGUIPlugin, CorrelationStage
from xicam.gui.widgets.views import DataSelectorView, StackedCanvasView
from xicam.plugins import GUILayout

from xicam.XPCS.projectors.nexus import project_nxXPCS


class SAXSPlugin(CorrelationStage):
    name = "SAXS"

    def __init__(self):
        super(SAXSPlugin, self).__init__()

    def appendCatalog(self, catalog: BlueskyRun, **kwargs):
        # catalog.metadata.update(self.schema())
        ensemble = Ensemble()
        ensemble.append_catalog(catalog)
        self.ensemble_model.add_ensemble(ensemble, project_nxXPCS)
