from xicam.SAXS.widgets.SAXSToolbar import SAXSToolbarBase, ROIs
from xicam.plugins import live_plugin
from xicam.gui.canvases import ImageIntentCanvas
from xicam.gui.widgets.imageviewmixins import LogScaleIntensity, ImageViewHistogramOverflowFix, \
    QCoordinates, Crosshair, BetterButtons, CenterMarker, ToolbarLayout


@live_plugin("ImageMixinPlugin")
class SAXSToolbarMixin(ToolbarLayout):
    def __init__(self, *args, **kwargs):
        toolbar = ROIs()
        super(SAXSToolbarMixin, self).__init__(*args, toolbar=toolbar, **kwargs)


@live_plugin("ImageMixinPlugin")
class SAXSImageIntentBlend(LogScaleIntensity, CenterMarker, BetterButtons, Crosshair, QCoordinates,
                           ImageViewHistogramOverflowFix, SAXSToolbarMixin):
    ...


class SAXSImageIntentCanvas(ImageIntentCanvas):
    def __init__(self, *args, **kwargs):
        super(SAXSImageIntentCanvas, self).__init__(*args, **kwargs)
