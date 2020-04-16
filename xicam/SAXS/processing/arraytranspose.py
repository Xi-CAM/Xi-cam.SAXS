from xicam.plugins.operationplugin import OperationPlugin, describe_input, \
                                          describe_output, output_names, categories
import numpy as np


@OperationPlugin
@describe_input('data', 'Input array of two or more dimensions')
@describe_input('axes', 'Axes to define transformation plane')
@describe_output('data', 'Transposed output array same dimensions as input array')
@output_names('data')
@categories('Transformations')

def transpose_array(data: np.ndarray,
                    axes: np.ndarray) -> np.ndarray:
    data = np.transpose(data, axes)
    return data

