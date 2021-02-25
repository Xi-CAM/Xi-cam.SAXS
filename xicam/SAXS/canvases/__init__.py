import numpy as np
from pyqtgraph import ImageView
from xarray import DataArray

from xicam.SAXS.widgets.SAXSToolbar import SAXSToolbarBase, ROIs
from xicam.plugins import manager as plugin_manager
from xicam.plugins import live_plugin
from xicam.gui.canvases import ImageIntentCanvas
from xicam.gui.widgets.imageviewmixins import LogScaleIntensity, ImageViewHistogramOverflowFix, \
    QCoordinates, Crosshair, BetterButtons, CenterMarker, ToolbarLayout, EwaldCorrected


@live_plugin("ImageMixinPlugin")
class SAXSToolbarMixin(ToolbarLayout):
    def __init__(self, *args, **kwargs):
        # Toolbar api will need view function or object...
        toolbar = ROIs()
        super(SAXSToolbarMixin, self).__init__(*args, toolbar=toolbar, **kwargs)


@live_plugin("ImageMixinPlugin")
class SAXSImageIntentBlend(LogScaleIntensity, CenterMarker, BetterButtons, Crosshair, QCoordinates, EwaldCorrected,
                           ImageViewHistogramOverflowFix, SAXSToolbarMixin):# LogButtons):
    ...


class SAXSImageIntentCanvas(ImageIntentCanvas):
    def __init__(self, *args, **kwargs):
        super(SAXSImageIntentCanvas, self).__init__(*args, **kwargs)

    def render(self, intent, **_):
        super(SAXSImageIntentCanvas, self).render(intent, mixins=["SAXSImageIntentBlend"])
        self.canvas_widget.setGeometry(intent.geometry)
