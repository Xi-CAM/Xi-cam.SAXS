from xicam.plugins import QWidgetPlugin
from pyqtgraph import ImageView, PlotItem
from xicam.core.data import NonDBHeader
from qtpy.QtWidgets import *
from qtpy.QtCore import *
from qtpy.QtGui import *
import numpy as np


class SAXSViewerPlugin(ImageView, QWidgetPlugin):
    def __init__(self, *args, **kwargs):

        # Add q axes
        self.axesItem = PlotItem()
        self.axesItem.setLabel('bottom', u'q (Å⁻¹)')  # , units='s')
        self.axesItem.setLabel('left', u'q (Å⁻¹)')
        self.axesItem.axes['left']['item'].setZValue(10)
        self.axesItem.axes['top']['item'].setZValue(10)
        if 'view' not in kwargs: kwargs['view'] = self.axesItem

        super(SAXSViewerPlugin, self).__init__()
        ImageView.__init__(self, *args, **kwargs)
        self.axesItem.invertY(False)

        # Setup axes reset button
        self.resetAxesBtn = QPushButton('Reset Axes')
        sizePolicy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.resetAxesBtn.sizePolicy().hasHeightForWidth())
        self.resetAxesBtn.setSizePolicy(sizePolicy)
        self.resetAxesBtn.setObjectName("resetBtn")
        self.ui.gridLayout.addWidget(self.resetAxesBtn, 2, 1, 1, 1)
        self.resetAxesBtn.clicked.connect(self.autoRange)

        # Setup LUT reset button
        self.resetLUTBtn = QPushButton('Reset LUT')
        sizePolicy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.resetLUTBtn.sizePolicy().hasHeightForWidth())
        self.resetLUTBtn.setSizePolicy(sizePolicy)
        self.resetLUTBtn.setObjectName("resetLUTBtn")
        self.ui.gridLayout.addWidget(self.resetLUTBtn, 2, 2, 1, 1)
        self.resetLUTBtn.clicked.connect(self.autoLevels)

        # Setup coordinates label
        self.coordinatesLbl = QLabel('--COORDINATES WILL GO HERE--')
        self.ui.gridLayout.addWidget(self.coordinatesLbl, 2, 0, 1, 1, alignment=Qt.AlignHCenter)

        # Use Viridis by default
        self.setPredefinedGradient('viridis')

    def quickMinMax(self, data):
        """
        Estimate the min/max values of *data* by subsampling. MODIFIED TO USE THE 99TH PERCENTILE instead of max.
        """
        while data.size > 1e6:
            ax = np.argmax(data.shape)
            sl = [slice(None)] * data.ndim
            sl[ax] = slice(None, None, 2)
            data = data[sl]
        return np.nanmin(data), np.nanpercentile(data, 99)

    def setHeader(self, header: NonDBHeader, *args, **kwargs):
        # make lazy array from document
        data = header.meta_array('image')
        kwargs['transform'] = QTransform(0,-1,1,0,0,data.shape[-2])

        super(SAXSViewerPlugin, self).setImage(img=data, *args, **kwargs)
