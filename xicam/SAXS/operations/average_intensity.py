import numpy as np
from xicam.SAXS.utils import get_label_array

from xicam.plugins.operationplugin import intent, operation, output_names, visible
from xicam.core.intents import PlotIntent


@operation
@output_names("times", "intensities", "images")
@intent(PlotIntent,
        "Average Intensity",
        output_map={"x": "times", "y": "intensities"},
        labels={"bottom": "t", "left": "I"},
        mixins=["ToggleSymbols"])
@visible('images', False)
@visible('rois', False)
def average_intensity(images: np.ndarray, rois: np.ndarray = None):
    # TODO: calculate labels from ROIs

    labels = get_label_array(images, rois=rois)

    # Trim the image based on labels, and resolve to memory
    si, se = np.where(np.flipud(labels))
    trimmed_images = np.asarray(images[:, si.min():si.max() + 1, se.min():se.max() + 1])
    trimmed_labels = np.asarray(np.flipud(labels)[si.min():si.max() + 1, se.min():se.max() + 1])

    averages = []
    if labels is not None:
        n_labels = int(labels.max())
        for label in range(1, n_labels + 1):
            masked_image = np.where(trimmed_labels == label, trimmed_images, np.zeros(trimmed_images[0].shape))
            averages.append(np.average(masked_image, axis=(-2, -1)))
    else:
        averages = np.average(trimmed_images, axis=(-2, -1))

    return np.asarray(range(len(images))), np.asarray(averages).squeeze(), images
