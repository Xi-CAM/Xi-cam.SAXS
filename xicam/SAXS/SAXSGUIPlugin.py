from databroker.core import BlueskyRun

from xicam.core.workspace import Ensemble
from .mixins import CorrelationGUIPlugin

projectors = []

try:
    from xicam.XPCS.projectors.nexus import project_nxXPCS
except ImportError:
    pass
else:
    projectors.append(project_nxXPCS)


def project_all(run_catalog:BlueskyRun):
    for projector in projectors:
        intents = projector(run_catalog)
        if intents:
            return intents


class SAXSPlugin(CorrelationGUIPlugin):
    name = 'SAXS'

    def appendCatalog(self, catalog: BlueskyRun, **kwargs):
        # catalog.metadata.update(self.schema())
        ensemble = Ensemble()
        ensemble.append_catalog(catalog)
        self.ensembleModel.add_ensemble(ensemble, project_all)
