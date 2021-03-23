import uuid

from pyFAI.detectors import ALL_DETECTORS
from scipy import constants

from xicam.SAXS.intents import SAXSImageIntent, GISAXSImageIntent
from xicam.SAXS.ontology import NXsas
from xicam.SAXS.patches.pyFAI import AzimuthalIntegrator
from xicam.core.data import ProjectionNotFound

PROJECTION_NAME = "NXSAS"
PROJECTION_KEYS = {
    "Detector Rotation": "",
    "Detector Translate": "",
    "detector_distance": "",
    "Beamline Energy": "",
    "Sample Translate": "",
    "Sample Rotation": "",
}

# Pinhole_X
# Pinhole_Y
# Sample Lift
# Sample Translate
# Sample Rotate Stepper (theta)
# Detector Rotate
# Det Translate
# Beamline Energy
# LS_LLH T A
# LS_LLH T B
# Mono energy,
# EPU energy

def extract_mapped_value(run_catalog, projection, key):
    stream = projection['projection'][PROJECTION_KEYS[key]]['stream']
    field = projection['projection'][PROJECTION_KEYS[key]]['field']
    return getattr(run_catalog, stream).to_dask()[field]

def project_NXsas(run_catalog):
    projection = next(
        filter(lambda projection: projection['name'] == PROJECTION_NAME, run_catalog.metadata['start']['projections']), None)

    if not projection:
        raise ProjectionNotFound(f"Could not find projection named '{PROJECTION_NAME}'.")

    data = extract_mapped_value(run_catalog, projection, NXsas.DATA_PROJECTION_KEY)

    detector_distance = extract_mapped_value(run_catalog, projection, NXsas.DISTANCE_PROJECTION_KEY)

    detector_rotation = extract_mapped_value(run_catalog, projection, NXsas.AZIMUTHAL_ANGLE_PROJECTION_KEY)

    beamline_energy = extract_mapped_value(run_catalog, projection, NXsas.ENERGY_PROJECTION_KEY)

    incidence_angle = extract_mapped_value(run_catalog, projection, NXsas.INCIDENCE_ANGLE_PROJECTION_KEY)

    detector_translate = extract_mapped_value(run_catalog, projection, NXsas.DETECTOR_TRANSLATION_X_PROJECTION_KEY)

    wavelength = 1.239842e-6 / beamline_energy  # convert from eV to meters

    # TODO: handle dynamic poni values

    poni1 = projection['configuration']['poni1']
    poni1 = poni1 - detector_translate
    poni2 = projection['configuration']['poni2']
    sdd = projection['configuration']['sdd']

    # Create detector from projection metadata
    detector_name = projection['configuration']['detector_name']
    detector_class = ALL_DETECTORS[detector_name]
    detector = detector_class()
    geometry = AzimuthalIntegrator(dist=sdd,
                                   poni1=poni1,
                                   poni2=poni2,
                                   rot2=detector_rotation,
                                   detector=detector,
                                   wavelength=wavelength)

    intents_list = []
    if projection['configuration']['geometry_mode'] == 'reflection':
        intents_list.append(GISAXSImageIntent(image=data,
                                              name='Scattering Image Data',
                                              geometry=geometry,
                                              incidence_angle=incidence_angle,
                                              match_key=uuid.uuid4()))
    else:
        intents_list.append(SAXSImageIntent(image=data,
                                            name='Scattering Image Data',
                                            geometry=geometry,
                                            match_key=uuid.uuid4()))

    return intents_list