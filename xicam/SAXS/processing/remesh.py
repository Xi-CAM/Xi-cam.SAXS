from xicam.plugins.operationplugin import operation, output_names, display_name, describe_input, describe_output, \
    categories
import numpy as np
import pyFAI
# FIXME: where is this package installed from?
import hipies


@operation
@display_name('Remesh')
@describe_input('data', 'Detector image')
@describe_input('geometry', 'pyFAI Geometry')
@describe_input('alpha_in', 'GISAXS incidence angle')
@describe_input('out_range', 'coordinates of output image')
@describe_input('resolution', 'resolution of output image')
@describe_input('coord_sys', 'Choice of coordinate system for output image')
@output_names('I', 'x', 'y', 'geometry')
@describe_output('I', 'remapped image')
@describe_output('x', 'X-coordinates output image')
@describe_output('y', 'Y-coordinates output image')
@describe_output('geometry', 'pyFAI geometry')

def image_remap(data: np.ndarray,
                geometry: pyFAI.geometry.Geometry,
                alpha_in: float,
                out_range: list=None,
                resolution: list=None,
                coord_sys: str='qp_qz') -> np.ndarray:

    I, x, y = hipies.remesh(data, geometry, alpha_in, out_range = out_range, 
                         res = resolution, coord_sys = coord_sys)
    dist = geometry._dist
    centerX = np.unravel_index(x.abs().argmin(), x.shape)[1]
    centerY = np.unravel_index(y.abs().argmin(), y.shape)[0]
    pixel = [geometry.get_pixel1(), geometry.get_pixel2()]
    center = [centerX * pixel[0], centerY * pixel[1]]
    geometry.setFit2D(geometry._dist, center[0], center[1])

    return I, x, y, geometry

