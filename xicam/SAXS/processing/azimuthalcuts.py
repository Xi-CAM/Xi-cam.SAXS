from xicam.plugins import ProcessingPlugin, Input, Output
import numpy as np


class AzimuthalCutPlugin(ProcessingPlugin):
    data = Input(description='Frame image data',
                 type=np.ndarray)

    center = Input(description='Array (same size as image) with 1 for masked pixels, and 0 for valid pixels',
                   type=np.ndarray)

    detector = Input(
        description='PyFAI detector instance; the geometry of the detector''s inactive area will be masked.',
        type=Detector)
    polygon = Input(description='Polygon shape to mask (interior is masked)')
    mask = Output(description='Mask array (1 is masked).',
                  type=np.ndarray)

    def evaluate(self):
        raise NotImplementedError
