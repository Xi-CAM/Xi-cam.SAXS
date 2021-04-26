from typing import List

import numpy as np
import pyqtgraph as pg
from camsaxs.remesh_bbox import q_from_geometry

from xicam.SAXS.patches.pyFAI import AzimuthalIntegrator


def get_label_array(images: np.ndarray, rois: np.ndarray = None, image_item: pg.ImageItem = None) -> np.ndarray:
    while images.ndim > 2:
        images = images[0]

    if rois is None:
        return np.ones_like(images)
    # Create zeros label array to insert new labels into (if multiple ROIs)
    label_array = np.zeros(images.shape)
    roi_masks = []
    for roi in rois:
        # TODO: Should label array be astype(np.int) (instead of float)?
        label = roi.getLabelArray(images, image_item)
        # Store the boolean mask of each label array
        roi_mask = label.astype(np.bool)
        roi_masks.append(roi_mask)
        # Grab the current label array maximum value (so we can increment multiple labels accordingly)
        label_array_max = label_array.max()
        label = np.where(label > 0, label + label_array_max, label)
        # For single roi, our max will be 0 (since label_array is just np.zeros so far, hasn't been modified)
        if label_array_max == 0:
            label_array = label
        else:
            # FIXME right now, if labels overlap, label integers are being added together (into a new label value)
            # Adjust any currently non-masked areas with the new label
            label_array = np.where(label_array == 0, label, label_array)
            #
            label_array = np.where(label_array > 0,
                                   np.where(label > 0, label, label_array),
                                   label_array)
            # label_array = np.where(label_array > 0,
            #                        label or label_array,
            #                        label_array)

    return label_array.astype(np.int)


def average_q_from_labels(labels: np.ndarray,
                          geometry: AzimuthalIntegrator,
                          transmission_mode: str,
                          incidence_angle=None) -> List[float]:
    # q_h, q_v
    q = q_from_geometry(labels.shape, geometry, transmission_mode == 'reflection', incidence_angle or 0.0)

    # TODO: how can we allow choosing between these different q values (q_h, q_v, q_norm)
    # q magnitude
    q = np.linalg.norm(q, axis=2)
    average_qs = [np.average(q, weights=(labels == i)) for i in range(1, labels.max() + 1)]
    # TODO: return a dict mapping labels to qs?
    return average_qs
