from xicam.plugins.operationplugin import operation
import numpy as np

sum = operation(np.sum, name="Sum", categories=(("General", "Mathematics"),))
