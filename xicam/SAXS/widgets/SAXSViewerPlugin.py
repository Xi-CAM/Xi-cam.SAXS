from xicam.plugins import QWidgetPlugin
from pyqtgraph import ImageView, PlotItem
from xicam.core.data import NonDBHeader
from qtpy.QtWidgets import *
from qtpy.QtCore import *
from qtpy.QtGui import *
import numpy as np
from xicam.core import msg
from xicam.gui.widgets.dynimageview import DynImageView
from xicam.gui.widgets.imageviewmixins import Crosshair, QCoordinates, CenterMarker, BetterButtons
import pyqtgraph as pg


class SAXSViewerPlugin(CenterMarker, BetterButtons, QCoordinates, Crosshair, DynImageView):

    def __init__(self, header: NonDBHeader = None, field: str = None, toolbar: QToolBar = None, *args, **kwargs):

        # Add q axes
        self.axesItem = PlotItem()
        self.axesItem.setLabel('bottom', u'q (Å⁻¹)')  # , units='s')
        self.axesItem.setLabel('left', u'q (Å⁻¹)')
        self.axesItem.axes['left']['item'].setZValue(10)
        self.axesItem.axes['top']['item'].setZValue(10)
        if 'view' not in kwargs: kwargs['view'] = self.axesItem

        super(SAXSViewerPlugin, self).__init__(**kwargs)
        self.axesItem.invertY(False)

        # Setup coordinates label
        # self.coordinatesLbl = QLabel('--COORDINATES WILL GO HERE--')
        # self.ui.gridLayout.addWidget(self.coordinatesLbl, 3, 0, 1, 1, alignment=Qt.AlignHCenter)

        # Setup mask layer
        self.maskimage = pg.ImageItem(opacity=.25)
        self.view.addItem(self.maskimage)

        # Setup calibration layer
        self.calibrantimage = pg.ImageItem(opacity=.25)
        self.view.addItem(self.calibrantimage)

        # Empty ROI for later use
        self.maskROI = pg.PolyLineROI([], closed=True, movable=False, pen=pg.mkPen(color='r', width=2))
        self.maskROI.handlePen = pg.mkPen(color='r', width=2)
        self.maskROI.handleSize = 10
        self.view.addItem(self.maskROI)

        # Connect toolbar handlers
        self.toolbar = toolbar
        if self.toolbar:
            self.toolbar.modegroup.triggered.connect(self.redraw)

        # Setup results cache
        self.results = []

        # Set header
        if header: self.setHeader(header, field)

    def setHeader(self, header: NonDBHeader, field: str, *args, **kwargs):
        self.header = header
        self.field = field
        # make lazy array from document
        data = None
        try:
            data = header.meta_array(field)
        except IndexError:
            msg.logMessage('Header object contained no frames with field ''{field}''.', msg.ERROR)

        if data:
            kwargs['transform'] = QTransform(1, 0, 0, -1, 0, data.shape[-2])
            super(SAXSViewerPlugin, self).setImage(img=data, *args, **kwargs)

    def setMaskImage(self, mask):
        if mask is not None:
            self.maskimage.setImage(mask, lut=np.array([[0, 0, 0, 0], [255, 0, 0, 255]]))
            self.maskimage.setTransform(QTransform(1, 0, 0, -1, 0, mask.shape[-2]))
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

        for result in self.results:
            try:
                if self.toolbar.cakeaction.isChecked():
                    self.setImage(result['cake'].value)
                    break
                elif self.toolbar.remeshaction.isChecked():
                    self.setImage(result['remesh'].value)  # TODO: add checkbox to toolbar
                    break
                elif 'inpaint' in result:
                    self.setImage(result['inpaint'].value)
                    break


            except TypeError:
                continue
        else:  # if self.toolbar.rawaction.isChecked():
            self.setHeader(self.header, self.field)

    def setResults(self, results):
        self.results = results
        self.redraw()


calibrantlut = np.array([[0, i, 0, i] for i in range(256)])
