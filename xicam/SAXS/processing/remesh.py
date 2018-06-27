from xicam.plugins import ProcessingPlugin, Input, Output
import numpy as np
import pyFAI
import hipies


class ImageRemap(ProcessingPlugin):
    name = 'Remesh'

    data = Input(description='Detector image', type=np.ndarray)
    geometry = InOut(description='pyFAI Geometry', type=pyFAI.geometry.Geometry)
    alphai = Input(description='GISAXS angle of incedence', type=float)
    out_range = Input(description='Coordinates of output image', type=list, default=None)
    resolution = Input(description='Resolution of output image', type=list, default=None)
    coord_sys = Input(description='Choice of coordinate system for output image', 
        type=str, default='qp_qz')


    qImage = Output(description='Remapped image', type=np.ndarray)
    xcrd = Output(description='X-coordinates output image', type=np.ndarray)
    ycrd = Output(description='Y-coordinates output image', type=np.ndarray)
    #hints = [ ]

    def evaluate(self):
        I, x, y = hipies.remesh(self.Image.value, self.geometry.value, self.alphai.value,
                    out_range = self.out_range.value, res = self.resolution.value,
                    coord_sys = self.coord_sys.value)
        self.qImage.value = I
        dist = self.geometry.value._dist
        centerX = np.unravel_index(x.abs().argmin(), x.shape)[1]
        centerY = np.unravel_index(y.abs().argmin(), y.shape)[0]
        pixel = [self.geometry.value.get_pixel1(), self.geometry.value.get_pixel2()]
        center = [ centerX * pixel[0], centerY * pixel[1])
        geometry.value.setFit2D(self.geometry.value._dist, center[0], center[1])
