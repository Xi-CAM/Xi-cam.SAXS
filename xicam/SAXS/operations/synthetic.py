import numpy as np
from xicam.plugins.operationplugin import operation, output_names
from xicam.plugins import live_plugin

@live_plugin("OperationPlugin")
@operation
@output_names("images")
def synthetic_image_series(images: np.ndarray, n: int = 10) -> np.ndarray:
    return np.array([images for i in range(n)])
    return np.array([np.random.poisson(images) for i in range(n)])