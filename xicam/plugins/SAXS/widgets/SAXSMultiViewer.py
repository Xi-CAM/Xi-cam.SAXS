from xicam.plugins import QWidgetPlugin
from pyqtgraph import ImageView, PlotItem
from xicam.core.data import NonDBHeader
from qtpy.QtWidgets import *
from qtpy.QtCore import *
from qtpy.QtGui import *
import numpy as np
from xicam.core import msg
from xicam.gui.widgets.tabview import TabView
from .SAXSViewerPlugin import SAXSViewerPlugin


class SAXSMultiViewerPlugin(QSplitter, QWidgetPlugin):
    def __init__(self, headermodel):
        super(SAXSMultiViewerPlugin, self).__init__()

        self.leftTabView = TabView()
        self.leftTabView.setWidgetClass(SAXSViewerPlugin)
        self.leftTabView.setModel(headermodel)
        self.rightTabView = TabView()
        self.rightTabView.setWidgetClass(SAXSViewerPlugin)
        self.rightTabView.setModel(headermodel)

        self.addWidget(self.leftTabView)
        self.addWidget(self.rightTabView)

    def __getattr__(self, attr):  ## implicitly wrap methods from leftViewer
        if hasattr(self.plotwidget, attr):
            m = getattr(self.leftViewer, attr)
            if hasattr(m, '__call__'):
                return m
        raise NameError(attr)
