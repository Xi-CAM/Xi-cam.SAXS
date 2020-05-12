from xicam.plugins.operationplugin import operation
import numpy as np
from pyFAI.ext.reconstruct import reconstruct


# Wraps the C implemented 'reconstruct' function to provide inspect metadata
def _reconstruct(ndarray_data: np.ndarray,
                 ndarray_mask: np.ndarray = None,
                 dummy: float = None,
                 delta_dummy: float = None):
    return reconstruct(ndarray_data, ndarray_mask, dummy, delta_dummy)


inpaint = operation(_reconstruct, name='Inpaint (pyFAI.ext.reconstruct)')
# TODO: add categories
