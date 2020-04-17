from xicam.plugins.operationplugin import operation
import numpy as np

array_transpose = operation(np.transpose, name="Transpose (Numpy)", categories=(("General", "Mathematics"),))
