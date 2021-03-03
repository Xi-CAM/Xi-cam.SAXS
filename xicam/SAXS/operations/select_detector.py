from enum import Enum
import numpy as np
from pyFAI.detectors import ALL_DETECTORS, Detector
from pyFAI.azimuthalIntegrator import AzimuthalIntegrator
from xicam.plugins.operationplugin import describe_input, describe_output, operation, output_names, display_name, units


def get_name(detector):
    if detector.aliases:
        name = detector.aliases[0]
    else:
        name = detector.__class__.__name__
    return name


# Remove 'detector' and sort by name
_detectors = {get_name(detector): detector
              for detector in ALL_DETECTORS.values()
              if detector is not Detector}
_sorted_detectors = dict(sorted(_detectors.items()))
DetectorEnum = Enum('Detector', _sorted_detectors)


@operation
@output_names()
@units("distance", "mm")
@units("center_x", "mm")
@units("center_y", "mm")
@units("tilt", "degrees")
@units("tilt_plane_rotation", "degrees")
@describe_input("distance", "Distance to detector center")
@describe_input("center_x", "")
@describe_input("center_y", "")
@describe_input("tilt", "")
@describe_input("tilt_plane_rotation", "")
def set_geometry(distance: float = 1,
                 center_x: float = 0,
                 center_y: float = 0,
                 tilt: float = 0.0,
                 tilt_plane_rotation: float = 0.0):
    ai = AzimuthalIntegrator()
    ai.setFit2D(distance, center_x, center_y, tilt, tilt_plane_rotation)
    return ai


# TODO: override parameter generation to disable detector selection when auto-mode is active
@operation
@display_name("Set Detector")
@output_names("azimuthal_integrator")
@describe_input("detector", "Detector to select in manual mode (automatic_mode = False).")
@describe_input("automatic_mode", "If True, automatically select a detector based on size heuristics; "
                                  "otherwise, uses the 'detector' input.")
@describe_input("binning_x", "Binning size of x dimension.")
@describe_input("binning_y", "Binning size of y dimension.")
@describe_input("azimuthal_integrator", "")
@describe_output("azimuthal_integrator", "")
def set_detector(detector: DetectorEnum = next(iter(DetectorEnum.__members__.values())).value,
                 automatic_mode: bool = True,
                 binning_x: int = 1,
                 binning_y: int = 1,
                 azimuthal_integrator: AzimuthalIntegrator = None,
                 data: np.ndarray = None) -> AzimuthalIntegrator:

    if automatic_mode:
        # Try to find best match based on the size
        selected_detector = guess_detector_by_shape(data.shape[-2:])

    else:
        selected_detector = detector()
        selected_detector.set_binning((binning_x, binning_y))

    ai = azimuthal_integrator or AzimuthalIntegrator()
    ai.detector = selected_detector
    return ai


def guess_detector_by_shape(shape):
    # for every detector known to pyFAI
    for name, detector in sorted(ALL_DETECTORS.items()):
        # if a shape limit is set
        if hasattr(detector, 'MAX_SHAPE'):
            if detector.MAX_SHAPE == shape:
                return detector()
        if hasattr(detector, 'BINNED_PIXEL_SIZE'):
            for binning in detector.BINNED_PIXEL_SIZE.keys():
                if shape == tuple(np.array(detector.MAX_SHAPE) / binning): # possibly needs to be reversed [::-1]
                    detector = detector()
                    detector.set_binning(binning)
                    return detector
    return None
