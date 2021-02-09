import numpy as np
from pyqtgraph import ImageView
from xarray import DataArray

from xicam.SAXS.widgets.SAXSToolbar import SAXSToolbarBase, ROIs
from xicam.plugins import manager as plugin_manager
from xicam.plugins import live_plugin
from xicam.gui.canvases import ImageIntentCanvas
from xicam.gui.widgets.imageviewmixins import LogScaleIntensity, ImageViewHistogramOverflowFix, \
    QCoordinates, Crosshair, BetterButtons, CenterMarker, ToolbarLayout


@live_plugin("ImageMixinPlugin")
class SAXSToolbarMixin(ToolbarLayout):
    def __init__(self, *args, **kwargs):
        # Toolbar api will need view function or object...
        toolbar = ROIs()
        super(SAXSToolbarMixin, self).__init__(*args, toolbar=toolbar, **kwargs)


@live_plugin("ImageMixinPlugin")
class SAXSImageIntentBlend(LogScaleIntensity, CenterMarker, BetterButtons, Crosshair, QCoordinates,
                           ImageViewHistogramOverflowFix, SAXSToolbarMixin):# LogButtons):
    ...


class SAXSImageIntentCanvas(ImageIntentCanvas):
    def __init__(self, *args, **kwargs):
        super(SAXSImageIntentCanvas, self).__init__(*args, **kwargs)

    def render(self, intent):
        if not self.canvas_widget:
            bases_names = intent.mixins or tuple()
            bases = map(lambda name: plugin_manager.type_mapping['ImageMixinPlugin'][name], bases_names)
            self.canvas_widget = type('ImageViewBlend', (*bases, ImageView), {})()
            self.canvas_widget.toolbar.view = self.canvas_widget
            self.layout().addWidget(self.canvas_widget)
            self.canvas_widget.imageItem.setOpts(imageAxisOrder='row-major')

        kwargs = intent.kwargs.copy()
        for key, value in kwargs.items():
            if isinstance(value, DataArray):
                kwargs[key] = np.asanyarray(value).squeeze()

        # TODO: add rendering logic for ROI intents
        return self.canvas_widget.setImage(np.asarray(intent.image).squeeze(), **kwargs)
