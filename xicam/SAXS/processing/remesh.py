from xicam.plugins import ProcessingPlugin, Input, Output
import numpy as np
import pyFAI
import camsaxs


class ImageRemap(ProcessingPlugin):
    Image = Input(description='Detector image', type=np.ndarray)
    geometry = Input(description='pyFAI Geometry', type=pyFAI.geometry.Geometry)
    alphai = Input(description='GISAXS angle of incedence', type=float)
    out_range = Input(description='Coordinates of output image', type=list, default=None)
    resolution = Input(description='Resolution of output image', type=list, default=None)
    coord_sys = Input(description='Choice of coordinate system for output image', 
        type=str, default='qp_qz')


    qImage = Output(description='Remapped image', type=np.ndarray)
    xcrd = Output(description='X-coordinates output image', type=np.ndarray)
    ycrd = Output(description='Y-coordinates output image', type=np.ndarray)

    def evaluate(self):
        I, x, y = camsaxs.remesh(self.Image.value, self.geometry.value, self.alphai.value,
                    out_range = self.out_range.value, res = self.resolution.value,
                    coord_sys = self.coord_sys.value)
        self.qImage.value = I
        self.xcrd.value = x
        self.ycrd.value = y
