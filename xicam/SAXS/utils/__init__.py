import numpy as np
import pyqtgraph as pg


def get_label_array(images: np.ndarray, rois: np.ndarray = None, image_item: pg.ImageItem = None) -> np.ndarray:
    if rois is None:
        return np.ones_like(images[0])
    # Create zeros label array to insert new labels into (if multiple ROIs)
    label_array = np.zeros(images[0].shape)
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
            print(f"{label_array_max + 1}: {(label_array == 1).sum()}")
            print()
        else:
            # FIXME right now, if labels overlap, label integers are being added together (into a new label value)
            # Adjust any currently non-masked areas with the new label
            label_array = np.where(label_array == 0, label, label_array)
            print(f"{1}: {(label_array == 1).sum()}")
            print(f"{2}: {(label_array == 2).sum()}")
            print()
            #
            label_array = np.where(label_array > 0,
                                   np.where(label > 0, label, label_array),
                                   label_array)
            # label_array = np.where(label_array > 0,
            #                        label or label_array,
            #                        label_array)
            print(f"1: {(label_array == 1).sum()}")
            print(f"2: {(label_array == 2).sum()}")
            print()

    return label_array.astype(np.int)
