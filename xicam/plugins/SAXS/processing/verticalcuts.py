from xicam.plugins import ProcessingPlugin, Input, Output
import numpy as np

class VerticalCutPlugin(ProcessingPlugin):
    data = Input(description='Frame image data', type=np.ndarray)
    qz = Input(description='qz coordinate corresponding to data', type=np.ndarray)

    mask = Input(description='Frame image data', type=np.ndarray, default=None)

    #Make qz range a single parameter, type = tuple
    qzminimum = Input(description='qz minimum limit',type=int)
    qzmaximum = Input(description='qz maximum limit',type=int)

    verticalcut = Output(description='mask (1 is masked) with dimension of data', type=np.ndarray)

    def evaluate(self):
        if self.mask.value is not None:
            self.verticalcut.value = np.logical_or(self.mask.value, self.qz < self.qzminimum.value, self.qz > self.qzmaximum.value)
        else:
            self.verticalcut.value = np.logical_or(self.qz < self.qzminimum.value, self.qz > self.qzmaximum.value)



def test_protocolcut(data, qz):
    t1 = VerticalCutPlugin()
    t1.data.value = data
    t1.qz.value = qz
    t1.qzminimum.value = 0.1
    t1.qzmaximum.value = 0.3
    t1.evaluate()
    print(t1.verticalcut.value())

    #assert t1.evaluate() == 3