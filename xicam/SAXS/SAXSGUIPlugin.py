from PyQt5.QtWidgets import QLabel
from databroker.core import BlueskyRun
from xicam.core import msg

from xicam.core.workspace import Ensemble
from xicam.core.data import ProjectionException
from xicam.SAXS.mixins import CorrelationGUIPlugin
from xicam.SAXS.projectors.nxcansas import project_nxcanSAS
from xicam.SAXS.projectors.edf import project_NXsas

projectors = [project_NXsas, project_nxcanSAS]

try:
    from xicam.XPCS.projectors.nexus import project_nxXPCS
except ImportError:
    pass
else:
    projectors.append(project_nxXPCS)


def project_all(run_catalog: BlueskyRun):
    for projector in projectors:
        try:
            intents = projector(run_catalog)
            if intents:
                return intents
        except ProjectionException:
            pass


class SAXSPlugin(CorrelationGUIPlugin):
    name = 'SAXS'

    def appendCatalog(self, catalog: BlueskyRun, **kwargs):
        # catalog.metadata.update(self.schema())
        ensemble = Ensemble()
        ensemble.append_catalog(catalog)
        self.ensemble_model.add_ensemble(ensemble, project_all)

