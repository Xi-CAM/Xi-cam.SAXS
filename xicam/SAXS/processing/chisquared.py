from xicam.plugins.operationplugin import operation, output_names, display_name, describe_input, describe_output, \
    categories, plot_hint
import numpy as np


@operation
@display_name('Chi squared')
@output_names('chi_squared')
@describe_input('dataA', 'Frame A image data')
@describe_input('dataB', 'Frame B image data')
@describe_output('chi_squared', 'Chi-squared difference between consecutive frames')
@categories(('General', 'Mathematics'))


def chi_squared(dataA: np.ndarray,
                dataB: np.ndarray) -> np.ndarray:
    chi_squared = (dataA - dataB) ** 2.
    
    return chi_squared


