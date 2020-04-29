rom
xicam.plugins.operationplugin
import operation, output_names, \
    display_name, describe_input, \
    describe_output, categories
import numpy as np


# TODO: Delete horizontalcuts.py, seems unused.
@operation
@display_name("Horizontal Cut")
@output_names('horizontal_cut')
@describe_input('data', 'Frame image data')
@describe_input('q_x', 'horizontal q coordinate corresponding to data')
@describe_input('mask', 'Frame image data')
@describe_input('q_x_min', 'horizontal q minimum limit')
@describe_input('q_x_max', 'horizontal q maximum limit')
@describe_output('horizontal_cut', 'mask (1 is masked) with dimension of data')
# TODO: add categories

def horizontal_cut(data: np.ndarray,
                   q_x: np.ndarray,
                   mask: np.ndarray = None,
                   q_x_min: int,
                   q_x_max: int) -> np.ndarray:
    if mask is not None:
        horizontal_cut = np.logical_or(mask, q_x < q_x_min, q_x > q_x_max)
    else:
        horizontal_cut = np.logical_or(q_x < q_x_min, q_x > q_x_max)
    return horizontal_cut
