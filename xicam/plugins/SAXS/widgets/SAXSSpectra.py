from qtpy.QtWidgets import *
from qtpy.QtCore import *
from xicam.plugins.WidgetPlugin import QWidgetPlugin
from pyqtgraph import PlotWidget
import numpy as np


class SAXSSpectra(QWidgetPlugin):
    name = 'SAXSSpectra'

    def __init__(self):
        super(SAXSSpectra, self).__init__()

        self.plotwidget = PlotWidget(
            labels={'bottom': 'q (\u212B\u207B\u00B9)', 'left': 'I (a.u.)', 'top': 'd (nm\u207B\u00B9)'})

        def tickStrings(values, scale, spacing):
            return ['{:.3f}'.format(.2 * np.pi / i) if i != 0 else '\u221E' for i in values]

        self.plotwidget.plotItem.axes['top']['item'].tickStrings = tickStrings
        self.toolbar = SAXSSpectraToolbar()

        hbox = QHBoxLayout()
        hbox.addWidget(self.toolbar)
        hbox.addWidget(self.plotwidget)
        self.setLayout(hbox)
        self.setContentsMargins(0, 0, 0, 0)
        hbox.setSpacing(0)

    def __getattr__(self, attr):  ## implicitly wrap methods from plotWidget
        if hasattr(self.plotwidget, attr):
            m = getattr(self.plotwidget, attr)
            if hasattr(m, '__call__'):
                return m
        raise NameError(attr)


class SAXSSpectraToolbar(QToolBar):
    def __init__(self):
        super(SAXSSpectraToolbar, self).__init__()

        self.addWidget(self.mkGroupToggle('q'))
        self.addWidget(self.mkGroupToggle('χ'))
        self.addWidget(self.mkGroupToggle('x'))
        self.addWidget(self.mkGroupToggle('z'))
        self.addSeparator()
        self.addAction('b/w')
        self.addAction('edit')

        self.setOrientation(Qt.Vertical)

    @staticmethod
    def mkGroupToggle(name: str):
        btn = QToolButton()
        btn.setCheckable(True)
        btn.setAutoExclusive(True)
        btn.setText(name)
        return btn
