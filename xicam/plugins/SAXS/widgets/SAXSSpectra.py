from qtpy.QtWidgets import *
from xicam.plugins.WidgetPlugin import QWidgetPlugin
from pyqtgraph import PlotWidget


class SAXSSpectra(QWidgetPlugin):
    name = 'SAXSSpectra'

    def __init__(self):
        super(SAXSSpectra, self).__init__()

        self.plotwidget = PlotWidget()
        self.toolbar = SAXSSpectraToolbar()

        hbox = QHBoxLayout()
        hbox.addWidget(self.plotwidget)
        hbox.addWidget(self.toolbar)
        self.setLayout(hbox)


class SAXSSpectraToolbar(QToolBar):
    def __init__(self):
        super(SAXSSpectraToolbar, self).__init__()

        self.addAction('Q')
        self.addAction('chi')
        self.addAction('x')
        self.addAction('z')
