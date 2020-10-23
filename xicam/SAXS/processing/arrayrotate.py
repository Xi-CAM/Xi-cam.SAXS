from xicam.plugins.operationplugin import operation
import numpy as np

array_rotate = operation(np.rot90, name="Rotate Array (numpy)", categories=(("General", "Mathematics"),))
