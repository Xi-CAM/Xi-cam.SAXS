from xicam.SAXS.widgets.SAXSToolbar import SAXSToolbarBase, ROIs
from xicam.plugins import manager as plugin_manager
from xicam.plugins import live_plugin
from xicam.gui.canvases import ImageIntentCanvas
from xicam.gui.widgets.imageviewmixins import LogScaleIntensity, ImageViewHistogramOverflowFix, \
    QCoordinates, Crosshair, BetterButtons, CenterMarker, ToolbarLayout, EwaldCorrected, ROICreator

from xicam.SAXS.widgets.imageviewmixins import BackgroundCorrected


@live_plugin("ImageMixinPlugin")
class SAXSToolbarMixin(ToolbarLayout):
    def __init__(self, *args, **kwargs):
        # Toolbar api will need view function or object...
        toolbar = ROIs()
        super(SAXSToolbarMixin, self).__init__(*args, toolbar=toolbar, **kwargs)


# FIXME: investigate EWaldCorrected (particularly ProcessingView) -- causes "tuple indexing error" on ProxyView when opening image
@live_plugin("ImageMixinPlugin")
class SAXSImageIntentBlend(BackgroundCorrected, LogScaleIntensity, CenterMarker, BetterButtons, Crosshair, QCoordinates,
                           ImageViewHistogramOverflowFix, ROICreator, EwaldCorrected):  # LogButtons):
    ...


class SAXSImageIntentCanvas(ImageIntentCanvas):
    def __init__(self, *args, **kwargs):
        super(SAXSImageIntentCanvas, self).__init__(*args, **kwargs)

    def render(self, intent, **_):
        super(SAXSImageIntentCanvas, self).render(intent, mixins=["SAXSImageIntentBlend"])
        if hasattr(intent, "geometry"):
            self.canvas_widget.setGeometry(intent.geometry)
        if hasattr(intent, "darks") and hasattr(self.canvas_widget, "set_darks"):
            self.canvas_widget.set_darks(intent._darks)
