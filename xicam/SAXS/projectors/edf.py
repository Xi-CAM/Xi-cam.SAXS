from xicam.SAXS.intents import SAXSImageIntent
from xicam.SAXS.ingestors.edf_ingestor import DATA_PROJECTION_KEY


def project_NXsas(run_catalog):
    projection = next(
        filter(lambda projection: projection['name'] == 'NXSAS', run_catalog.metadata['start']['projections']))

    data_stream = projection['projection'][DATA_PROJECTION_KEY]['stream']
    data_field = projection['projection'][DATA_PROJECTION_KEY]['field']

    data = getattr(run_catalog, data_stream).to_dask().rename({data_field: DATA_PROJECTION_KEY})

    intents_list = []
    intents_list.append(SAXSImageIntent(image=data[DATA_PROJECTION_KEY], item_name='Scattering Image Data'))

    return intents_list