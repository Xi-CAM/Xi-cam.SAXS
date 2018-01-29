from qtpy.QtWidgets import *
from qtpy.QtGui import *
from qtpy.QtCore import *
from xicam.plugins.WidgetPlugin import QWidgetPlugin
from pyqtgraph import PlotWidget
import numpy as np
from xicam.gui.static import path


class SAXSSpectra(QWidgetPlugin):
    name = 'SAXSSpectra'

    def __init__(self):
        super(SAXSSpectra, self).__init__()

        self.plotwidget = PlotWidget(
            labels={'bottom': 'q (\u212B\u207B\u00B9)', 'left': 'I (a.u.)', 'top': 'd (nm)'})

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


class SAXSSpectraToolbar(QWidget):
    def __init__(self):
        super(SAXSSpectraToolbar, self).__init__()

        layout = QVBoxLayout()
        modetoolbar = QToolBar()
        optionstoolbar = QToolBar()
        layout.addWidget(modetoolbar)
        layout.addWidget(optionstoolbar)
        self.setLayout(layout)
        layout.setStretch(0, 2)
        layout.setStretch(1, 1)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        self.modeActionGroup = QActionGroup(self)
        qbtn = self.mkGroupToggle('icons/q.png', text='q (Azimuthal) Integration')
        qbtn.setChecked(True)
        modetoolbar.addAction(qbtn)
        modetoolbar.addAction(self.mkGroupToggle('icons/chi.png', text='χ (chi/Radial) Integration'))
        modetoolbar.addAction(self.mkGroupToggle('icons/x.png', text='X (Horizontal) Integration'))
        modetoolbar.addAction(self.mkGroupToggle('icons/z.png', text='Z (Vertical) Integration'))
        modetoolbar.addAction(self.mkGroupToggle('icons/G.png', text='Guinier Plot'))
        modetoolbar.addAction(self.mkGroupToggle('icons/P.png', text='Porod Plot'))
        modetoolbar.addAction(self.mkGroupToggle('icons/Iq2.png', text='I×q\u00B2'))
        modetoolbar.addAction(self.mkGroupToggle('icons/Iq3.png', text='I×q\u00B3'))
        modetoolbar.addAction(self.mkGroupToggle('icons/Iq4.png', text='I×q\u0074'))
        modetoolbar.addAction(self.mkGroupToggle('icons/gofr.png', text='Electron Density Correlation Function'))
        modetoolbar.addAction(self.mkGroupToggle('icons/gofrvec.png', text='Pair Distribution Function'))

        multiplot = QAction(self)
        multiplot.setIcon(QIcon(str(path('icons/multiplot.png'))))
        multiplot.setText('Plot Series')
        multiplot.setCheckable(True)
        optionstoolbar.addSeparator()
        optionstoolbar.addAction(multiplot)
        optionstoolbar.addAction(QIcon(str(path('icons/blackwhite.png'))), 'Toggle Theme')
        optionstoolbar.addAction(QIcon(str(path('icons/configure.png'))), 'Configure Plot')

        optionstoolbar.setOrientation(Qt.Vertical)
        modetoolbar.setOrientation(Qt.Vertical)

    def mkGroupToggle(self, iconpath: str = None, text=None):
        actn = QAction(self)
        if iconpath: actn.setIcon(QIcon(QPixmap(str(path(iconpath)))))
        if text: actn.setText(text)
        actn.setCheckable(True)
        actn.setActionGroup(self.modeActionGroup)
        return actn
