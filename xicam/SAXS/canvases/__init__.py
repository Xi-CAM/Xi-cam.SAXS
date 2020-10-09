from xicam.gui.canvases import ImageIntentCanvas
from xicam.gui.widgets.imageviewmixins import LogScaleIntensity, XArrayView, ImageViewHistogramOverflowFix, \
    QCoordinates, Crosshair, BetterButtons, CenterMarker


class SAXSImageIntentBlend(LogScaleIntensity, XArrayView, CenterMarker, BetterButtons, Crosshair, QCoordinates,
                           ImageViewHistogramOverflowFix):
    ...


class SAXSImageIntentCanvas(ImageIntentCanvas, SAXSImageIntentBlend):
    def __init__(self, *args, **kwargs):
        super(SAXSImageIntentCanvas, self).__init__(*args, **kwargs)