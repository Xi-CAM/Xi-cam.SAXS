from xicam.plugins import QWidgetPlugin
from pyqtgraph import ImageView, PlotItem
from xicam.core.data import NonDBHeader
from qtpy.QtWidgets import *
from qtpy.QtCore import *
from qtpy.QtGui import *
import numpy as np
from xicam.core import msg
from xicam.plugins import manager as pluginmanager
from xicam.gui.widgets.dynimageview import DynImageView
from xicam.gui.widgets.imageviewmixins import Crosshair, QCoordinates, CenterMarker, BetterButtons, EwaldCorrected, \
    LogScaleIntensity, DisplayMode, CatalogView, XArrayView, ImageViewHistogramOverflowFix
import pyqtgraph as pg


# TODO LogScaleIntensity
class SAXSViewerPluginBase(CenterMarker, BetterButtons, Crosshair, QCoordinates, DynImageView, CatalogView, ImageViewHistogramOverflowFix):

    def __init__(self, *args, **kwargs):

        super(SAXSViewerPluginBase, self).__init__(*args, **kwargs)
        self.axesItem.invertY(False)

        # Setup coordinates label
        # self.coordinatesLbl = QLabel('--COORDINATES WILL GO HERE--')
        # self.ui.gridLayout.addWidget(self.coordinatesLbl, 3, 0, 1, 1, alignment=Qt.AlignHCenter)

        # Setup mask layer
        # TODO -- put in mixin
        self.maskimage = pg.ImageItem(opacity=.25, axisOrder='row-major')
        self.view.addItem(self.maskimage)

        # Setup calibration layer
        # TODO -- put in mixin
        self.calibrantimage = pg.ImageItem(opacity=.25)
        self.view.addItem(self.calibrantimage)

        # Empty ROI for later use
        # TODO -- refactor poly masking
        self.maskROI = pg.PolyLineROI([], closed=True, movable=False, pen=pg.mkPen(color='r', width=2))
        self.maskROI.handlePen = pg.mkPen(color='r', width=2)
        self.maskROI.handleSize = 10
        self.view.addItem(self.maskROI)

    def setMaskImage(self, mask):
        if mask is not None:
            self.maskimage.setImage(mask, lut=np.array([[0, 0, 0, 0], [255, 0, 0, 255]]))
            # self.maskimage.setTransform(QTransform(1, 0, 0, -1, 0, mask.shape[-2]))
        else:
            self.maskimage.clear()

    def setCalibrantImage(self, data):
        if data is not None:
            self.calibrantimage.setImage(data, lut=calibrantlut)
            # self.calibrantimage.setTransform(QTransform(0, 1, 1, 0, 0, 0))
        else:
            self.calibrantimage.clear()

    def redraw(self):
        if not self.parent().currentWidget() == self: return  # Don't redraw when not shown

        self.setHeader(self.header, self.field)

    def setResults(self, results):
        self.results = results
        self.redraw()


calibrantlut = np.array([[0, i, 0, i] for i in range(256)])


class SAXSCalibrationViewer(SAXSViewerPluginBase):
    pass


class SAXSMaskingViewer(SAXSViewerPluginBase):
    pass


class SAXSCompareViewer(SAXSViewerPluginBase):
    pass


class SAXSReductionViewer(EwaldCorrected, SAXSViewerPluginBase):
    def __init__(self, *args, toolbar: QToolBar = None, **kwargs):
        super(SAXSReductionViewer, self).__init__(*args, **kwargs)

        # Connect toolbar handlers
        self.toolbar = toolbar
        if self.toolbar:
            self.toolbar.modegroup.triggered.connect(self.setDisplayMode)
            # TODO -- re-connect the sigDeviceChanged outside of here
            # self.toolbar.sigDeviceChanged.connect(self.deviceChanged)
            # self.toolbar.sigDeviceChanged.connect(self.fieldChanged)


    def setDisplayMode(self, mode):
        if mode.text() == 'Wrap Ewald Sphere':
            mode = DisplayMode.remesh
        elif mode.text() == 'Raw':
            mode = DisplayMode.raw
        elif mode.text() == 'Cake (q/chi plot)':
            mode = DisplayMode.cake

        EwaldCorrected.setDisplayMode(self, mode)
