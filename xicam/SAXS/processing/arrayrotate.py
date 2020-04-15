from xicam.plugins.operationplugin import OperationPlugin, describe_input, describe_output, \
     output_names, categories
import numpy as np

@OperationPlugin
@describe_input('data', 'Input array of two or more dimensions')
@describe_input('number_of_rotation', 'Number of times the array is rotated by 90 degrees')
@describe_input('axis_of_rotation', 'The array is rotated in the plane defined by the axes. Axes must be different.')
@describe_output('data', 'Output array of two or more dimensions')
@output_names('data')
@categories('Transformations')


def rotate_array(data: np.ndarray,
                number_of_rotation: int = 1,
                axis_of_rotation: np.ndarray = (0,1)) -> np.ndarray:
    
     data = np.rot90(data, number_of_rotation, axis_of_rotation)
     return data



