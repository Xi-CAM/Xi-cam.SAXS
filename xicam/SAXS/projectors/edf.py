import uuid

import numpy as np
from pyFAI.detectors import ALL_DETECTORS
from scipy import constants

from xicam.SAXS.intents import SAXSImageIntent, GISAXSImageIntent
from xicam.SAXS.ontology import NXsas
from xicam.SAXS.patches.pyFAI import AzimuthalIntegrator
from xicam.core.data import ProjectionNotFound
from xicam.core import msg
from xicam.SAXS.ontology.NXsas import DATA_PROJECTION_KEY
from xicam.plugins import manager as plugin_manager

PROJECTION_NAME = "NXsas"
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
    # TODO: should safely handle if key not found in projection
    if projection['projection'][key]['type'] == 'linked':
        stream = projection['projection'][key]['stream']
        field = projection['projection'][key]['field']
        return getattr(run_catalog, stream).to_dask()[field]
    elif projection['projection'][key]['type'] == 'static':
        return projection['projection'][key]['value']


def project_NXsas(run_catalog):
    projection = next(
        filter(lambda projection: projection['name'] == PROJECTION_NAME, run_catalog.metadata['start']['projections']),
        None)

    if not projection:
        raise ProjectionNotFound(f"Could not find projection named '{PROJECTION_NAME}'.")

    data = extract_mapped_value(run_catalog, projection, NXsas.DATA_PROJECTION_KEY)

    # try to extract dark image
    device_name = projection['projection'][DATA_PROJECTION_KEY]['field']
    try:
        darks = run_catalog.dark.to_dask()[device_name]
    except (AttributeError, KeyError) as e:
        darks = None
        msg.logMessage(e, level=msg.WARNING)

    # handle case where we don't have info to construct a geometry
    incidence_angle = None

    calibration_settings = plugin_manager.get_plugin_by_name('xicam.SAXS.calibration', 'SettingsPlugin')

    try:
        incidence_angle = extract_mapped_value(run_catalog, projection, NXsas.INCIDENCE_ANGLE_PROJECTION_KEY)

        detector_rotation = extract_mapped_value(run_catalog, projection, NXsas.AZIMUTHAL_ANGLE_PROJECTION_KEY)

        beamline_energy = extract_mapped_value(run_catalog, projection, NXsas.ENERGY_PROJECTION_KEY)

        detector_translate_x = extract_mapped_value(run_catalog, projection, NXsas.DETECTOR_TRANSLATION_X_PROJECTION_KEY)
        detector_translate_y = extract_mapped_value(run_catalog, projection, NXsas.DETECTOR_TRANSLATION_Y_PROJECTION_KEY)

        wavelength = 1.239842e-6 / beamline_energy  # convert from eV to meters

        # TODO: handle dynamic poni values
        poni1 = projection['configuration']['poni1'] - detector_translate_x
        poni2 = projection['configuration']['poni2'] - detector_translate_y

        sdd = projection['configuration']['sdd']

        # These are static values, take first one; using max() to get scalar value
        poni1 = poni1[0].values.max()
        rot2 = detector_rotation[0].values.max()
        wavelength = wavelength[0].values.max()
        incidence_angle = incidence_angle[0].values.max()

        # Create detector from projection metadata
        detector_name = projection['configuration']['detector_name']
        detector_class = ALL_DETECTORS[detector_name]
        detector = detector_class()

        # Convert poni from pixel to meters
        poni1 *= detector.get_pixel1()
        poni2 *= detector.get_pixel2()

        geometry = AzimuthalIntegrator(dist=sdd,
                                       poni1=poni1,
                                       poni2=poni2,
                                       rot2=-np.radians(rot2),  # Convert to radians, account for upward rotation
                                       detector=detector,
                                       wavelength=wavelength)


        calibration_settings.setAI(geometry, device_name)

    except (AttributeError, KeyError) as e:
        geometry = None
        msg.logMessage(e, level=msg.WARNING)

    if geometry is None and device_name in calibration_settings.AIs:
        geometry = calibration_settings.AI(device_name)

    intents_list = []
    if projection['configuration'].get('geometry_mode') == 'reflection':
        intents_list.append(GISAXSImageIntent(image=data,
                                              darks=darks,
                                              name=f"GISAXS 〈{run_catalog.metadata['start']['sample_name']}〉",
                                              geometry=geometry,
                                              incidence_angle=incidence_angle,
                                              match_key=uuid.uuid4(),
                                              device_name=device_name), )
    else:
        intents_list.append(SAXSImageIntent(image=data,
                                            darks=darks,
                                            name=f"SAXS 〈{run_catalog.metadata['start']['sample_name']}〉",
                                            geometry=geometry,
                                            match_key=uuid.uuid4(),
                                            device_name=device_name))

    return intents_list
