from xicam.gui.canvases import ImageIntentCanvas
from xicam.gui.widgets.imageviewmixins import LogScaleIntensity, ImageViewHistogramOverflowFix, \
    QCoordinates, Crosshair, BetterButtons, CenterMarker


class SAXSImageIntentBlend(LogScaleIntensity, CenterMarker, BetterButtons, Crosshair, QCoordinates,
                           ImageViewHistogramOverflowFix):
    ...


class SAXSImageIntentCanvas(ImageIntentCanvas, SAXSImageIntentBlend):
    def __init__(self, *args, **kwargs):
        super(SAXSImageIntentCanvas, self).__init__(*args, **kwargs)