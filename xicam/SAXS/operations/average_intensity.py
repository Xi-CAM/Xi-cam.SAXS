import numpy as np
from xicam.SAXS.utils import get_label_array

from xicam.plugins.operationplugin import intent, operation, output_names, visible
from xicam.core.intents import PlotIntent


@operation
@output_names("times", "intensities", "images")
@intent(PlotIntent,
        "Average Intensity",
        output_map={"x": "times", "y": "intensities"},
        labels={"bottom": "t", "left": "I"})
@visible('images', False)
@visible('rois', False)
def average_intensity(images: np.ndarray, rois: np.ndarray = None):
    # TODO: calculate labels from ROIs
    averages = []
    labels = get_label_array(images, rois=rois)
    if labels is not None:
        n_labels = int(labels.max())
        for label in range(1, n_labels + 1):
            masked_image = np.where(labels == label, images, np.zeros(images[0].shape))
            averages.append(np.average(masked_image, axis=(-2, -1)))
    else:
        for image in images:
            averages = np.average(images, axis=(-2, -1))
            averages.append(np.average(image))

    return np.asarray(range(len(images))), np.asarray(averages).squeeze(), images
