from qtpy.QtWidgets import *
from qtpy.QtGui import *
from qtpy.QtCore import *
from xicam.plugins.WidgetPlugin import QWidgetPlugin
from pyqtgraph import PlotWidget
import numpy as np
from xicam.gui.static import path
from xicam.core.execution.workflow import Workflow
from xicam.core import msg
from functools import partial
from copy import deepcopy
from typing import Tuple


class SAXSSpectra(QWidgetPlugin):
    name = 'SAXSSpectra'

    def __init__(self, workflow: Workflow):
        super(SAXSSpectra, self).__init__()

        self._cache = {}  # cache is dict to allow future use of other keys as 'time' index
        self.workflow = workflow

        self.plotwidget = PlotWidget(
            labels={'bottom': 'q (\u212B\u207B\u00B9)', 'left': 'I (a.u.)', 'top': 'd (nm)'})

        def tickStrings(values, scale, spacing):
            return ['{:.3f}'.format(.2 * np.pi / i) if i != 0 else '\u221E' for i in values]

        self.plotwidget.plotItem.axes['top']['item'].tickStrings = tickStrings
        self.toolbar = SAXSSpectraToolbar()
        self.toolbar.sigPlotCache.connect(self.replot_all)

        hbox = QHBoxLayout()
        hbox.addWidget(self.toolbar)
        hbox.addWidget(self.plotwidget)
        self.setLayout(hbox)
        self.setContentsMargins(0, 0, 0, 0)
        hbox.setSpacing(0)

    def setResult(self, result: Tuple[dict]):
        self.clear()
        self._cache[0] = tuple({k: v.value for k, v in r.items()} for r in result)
        self.replot_all()

    def appendResult(self, result):
        result_cache = tuple({k: v.value for k, v in r.items()} for r in result)
        self._cache[len(self._cache)] = result_cache
        self.plot_mode(result_cache)

    def plot_mode(self, resultset):
        mode = self.toolbar.modeActionGroup.checkedAction().text()
        for result in resultset:
            try:
                if mode == 'q (Azimuthal) Integration':
                    self.plot(result['q'], result['I'])
                    break
                elif mode == 'χ (chi/Radial) Integration':
                    self.plot(result['chi'], result['I'])
                    break
                elif mode == 'X (Horizontal) Integration':
                    self.plot(result['qx'], result['I'])
                    break
                elif mode == 'Z (Vertical) Integration':
                    self.plot(result['qz'], result['I'])
                    break
            except KeyError:
                pass
        else:
            ex = KeyError('No data found in result')
            msg.logError(ex)

    def replot_all(self, checked=True):
        if not checked: return
        self.plotwidget.clear()
        for result in self._cache.values():
            self.plot_mode(result)

    def clear(self):
        self.plotwidget.clear()
        self._cache = {}

    def __getattr__(self, attr):  # implicitly wrap methods from plotWidget
        if hasattr(self.plotwidget, attr):
            m = getattr(self.plotwidget, attr)
            if hasattr(m, '__call__'):
                return m
        raise NameError(attr)


class SAXSSpectraToolbar(QWidget):
    sigPlotCache = Signal()
    sigDoWorkflow = Signal()

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
        qbtn = self.mkGroupToggle('icons/q.png', text='q (Azimuthal) Integration', receiver=self.sigPlotCache.emit)
        qbtn.setChecked(True)
        modetoolbar.addAction(qbtn)
        modetoolbar.addAction(
            self.mkGroupToggle('icons/chi.png', text='χ (chi/Radial) Integration', receiver=self.sigPlotCache.emit))
        modetoolbar.addAction(
            self.mkGroupToggle('icons/x.png', text='X (Horizontal) Integration', receiver=self.sigPlotCache.emit))
        modetoolbar.addAction(
            self.mkGroupToggle('icons/z.png', text='Z (Vertical) Integration', receiver=self.sigPlotCache.emit))
        modetoolbar.addAction(self.mkGroupToggle('icons/G.png', text='Guinier Plot', receiver=self.sigPlotCache.emit))
        modetoolbar.addAction(self.mkGroupToggle('icons/P.png', text='Porod Plot', receiver=self.sigPlotCache.emit))
        modetoolbar.addAction(self.mkGroupToggle('icons/Iq2.png', text='I×q\u00B2', receiver=self.sigPlotCache.emit))
        modetoolbar.addAction(self.mkGroupToggle('icons/Iq3.png', text='I×q\u00B3', receiver=self.sigPlotCache.emit))
        modetoolbar.addAction(self.mkGroupToggle('icons/Iq4.png', text='I×q\u0074', receiver=self.sigPlotCache.emit))
        modetoolbar.addAction(self.mkGroupToggle('icons/gofr.png', text='Electron Density Correlation Function',
                                                 receiver=self.sigPlotCache.emit))
        modetoolbar.addAction(
            self.mkGroupToggle('icons/gofrvec.png', text='Pair Distribution Function', receiver=self.sigPlotCache.emit))

        self.multiplot = QAction(self)
        self.multiplot.setIcon(QIcon(str(path('icons/multiplot.png'))))
        self.multiplot.setText('Plot Series')
        self.multiplot.setCheckable(True)
        self.multiplot.triggered.connect(self.sigDoWorkflow)
        optionstoolbar.addSeparator()
        optionstoolbar.addAction(self.multiplot)
        optionstoolbar.addAction(QIcon(str(path('icons/blackwhite.png'))), 'Toggle Theme')
        optionstoolbar.addAction(QIcon(str(path('icons/configure.png'))), 'Configure Plot')

        optionstoolbar.setOrientation(Qt.Vertical)
        modetoolbar.setOrientation(Qt.Vertical)

    def mkGroupToggle(self, iconpath: str = None, text=None, receiver=None):
        actn = QAction(self)
        if iconpath: actn.setIcon(QIcon(QPixmap(str(path(iconpath)))))
        if text: actn.setText(text)
        if receiver: actn.triggered.connect(receiver)
        actn.setCheckable(True)
        actn.setActionGroup(self.modeActionGroup)
        return actn
