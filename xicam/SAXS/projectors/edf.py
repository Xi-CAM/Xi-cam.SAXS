import uuid

from xicam.SAXS.intents import SAXSImageIntent
from xicam.SAXS.ontology import NXsas
from xicam.core.data import ProjectionNotFound


def project_NXsas(run_catalog):
    projection = next(
        filter(lambda projection: projection['name'] == 'NXSAS', run_catalog.metadata['start']['projections']), None)

    if not projection:
        raise ProjectionNotFound("Could not find projection named 'NXSAS'.")

    data_stream = projection['projection'][NXsas.DATA_PROJECTION_KEY]['stream']
    data_field = projection['projection'][NXsas.DATA_PROJECTION_KEY]['field']

    data = getattr(run_catalog, data_stream).to_dask().rename({data_field: NXsas.DATA_PROJECTION_KEY})

    intents_list = []
    intents_list.append(SAXSImageIntent(image=data[NXsas.DATA_PROJECTION_KEY],
                                        name='Scattering Image Data',
                                        match_key=uuid.uuid4()))

    return intents_list