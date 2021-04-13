from xicam.SAXS.intents import SAXSImageIntent
from xicam.core.data import ProjectionNotFound
from xicam.core.data.bluesky_utils import display_name
from xicam.core.intents import ImageIntent
from xicam.SAXS.ingestors.nxcansas import I_PROJECTION_KEY, QX_PROJECTION_KEY, QY_PROJECTION_KEY


# TODO: Intent for experimental geometry (SAXSImageIntent will include the geometry)
#  allow NOT having a geometry as well
def project_nxcanSAS(run_catalog):
    projection = next(
        filter(lambda projection: projection['name'] == 'NXcanSAS', run_catalog.metadata['start'].get('projections', [])), None)
    if not projection:
        raise ProjectionNotFound("Could not find projection 'NXcanSAS'.")
    catalog_name = display_name(run_catalog).split(" ")[0]

    data_stream = projection['projection'][I_PROJECTION_KEY]['stream']
    data_field = projection['projection'][I_PROJECTION_KEY]['field']
    qx_stream = projection['projection'][QX_PROJECTION_KEY]['stream']
    qx_field = projection['projection'][QX_PROJECTION_KEY]['field']
    qy_stream = projection['projection'][QY_PROJECTION_KEY]['stream']
    qy_field = projection['projection'][QY_PROJECTION_KEY]['field']

    data = getattr(run_catalog, data_stream).to_dask().rename({data_field: I_PROJECTION_KEY})
    qx = getattr(run_catalog, data_stream).to_dask().rename({qx_field: QX_PROJECTION_KEY})
    qy = getattr(run_catalog, data_stream).to_dask().rename({qy_field: QY_PROJECTION_KEY})

    intents_list = []
    # TODO: construct geometry from qx / qy, then pass into intent below
    intents_list.append(SAXSImageIntent(image=data, item_name='Intensity'))

    return intents_list