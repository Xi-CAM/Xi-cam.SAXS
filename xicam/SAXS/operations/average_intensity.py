import numpy as np
from xicam.SAXS.utils import get_label_array

from xicam.plugins.operationplugin import intent, operation, output_names
from xicam.core.intents import PlotIntent


@operation
@output_names("times", "intensities", "images")
@intent(PlotIntent,
        "Average Intensity",
        output_map={"x": "times", "y": "intensities"},
        labels={"bottom": "t", "left": "I"})
def average_intensity(images: np.ndarray, rois: np.ndarray = None):
    # TODO: calculate labels from ROIs
    averages = []
    labels = get_label_array(images, rois=rois)
    if labels is not None:
        n_labels = int(labels.max())
        label_averages = []
        for label in range(1, n_labels + 1):
            for image in images:
                masked_image = np.where(labels == label, image, np.zeros(image.shape))
                label_averages.append(np.average(masked_image))
            averages.append(label_averages)
    else:
        for image in images:
            averages.append(np.average(image))

    return np.asarray((range(len(images)))), np.asarray(averages).squeeze(), images
