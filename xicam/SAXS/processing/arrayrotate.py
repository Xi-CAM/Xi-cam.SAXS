from xicam.plugins.operationplugin import operation
import numpy as np

rotate_array = operation(np.rot90, name="Rotate Array", categories=(("General", "Mathematics"),))
