from databroker.core import BlueskyRun

from xicam.core.workspace import Ensemble
from xicam.XPCS.projectors.nexus import project_nxXPCS

from xicam.SAXS.mixins import CorrelationGUIPlugin, TemporarySAXSGUIPlugin


class SAXSPlugin(TemporarySAXSGUIPlugin, CorrelationGUIPlugin):

    def appendCatalog(self, catalog: BlueskyRun, **kwargs):
        # catalog.metadata.update(self.schema())
        ensemble = Ensemble()
        ensemble.append_catalog(catalog)
        self.ensembleModel.add_ensemble(ensemble, project_nxXPCS)
