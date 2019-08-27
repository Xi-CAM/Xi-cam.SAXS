from qtpy.QtWidgets import *
from qtpy.QtGui import *
from qtpy.QtCore import *
from xicam.plugins.widgetplugin import QWidgetPlugin
from pyqtgraph import PlotWidget, PlotDataItem, intColor, mkPen
from pyqtgraph.graphicsItems.LegendItem import ItemSample
import numpy as np
from xicam.gui.static import path
from xicam.core.execution.workflow import Workflow
from typing import Tuple


class SAXSSpectra(QTabWidget, QWidgetPlugin):
    name = 'SAXSSpectra'

    def __init__(self, workflow: Workflow, toolbar: QToolBar):
        super(SAXSSpectra, self).__init__()

        self._cache = {}  # cache is dict to allow future use of other keys as 'time' index
        self.workflow = workflow

        self.toolbar = toolbar
        self.toolbar.sigPlotCache.connect(self.replot_all)

        # self.legend = self.plotwidget.addLegend()

        # hbox = QHBoxLayout()
        # # hbox.addWidget(self.toolbar)
        # hbox.addWidget(self.plotwidget)
        # self.setLayout(hbox)
        # self.setContentsMargins(0, 0, 0, 0)
        # hbox.setSpacing(0)

    def setResult(self, result: Tuple[dict]):
        self.clear_all()
        self._cache[0] = tuple({k: v.value for k, v in r.items()} for r in result)
        self.replot_all()

    def appendResult(self, result):
        result_cache = tuple({k: v.value for k, v in r.items()} for r in result)
        self._cache[len(self._cache)] = result_cache
        self.plot_mode(result_cache)

    def plot_mode(self, resultset):
        self.clear()

        for result in resultset:
            name = next(iter(result.keys()))
            plotwidget = PlotWidget(
                labels={'bottom': 'q (\u212B\u207B\u00B9)', 'left': 'I (a.u.)', 'top': 'd (nm)'})

            def tickStrings(values, scale, spacing):
                return ['{:.3f}'.format(.2 * np.pi / i) if i != 0 else '\u221E' for i in values]

            plotwidget.plotItem.axes['top']['item'].tickStrings = tickStrings

            plotwidget.plot(*list(output.value for output in result.values()), name=name)

            self.addTab(plotwidget, name)

        #
        # checkedindices = self.toolbar.reductionModesModel.checkedIndices()
        # for name, xoutput, youtput in [
        #     (checkedindex.internalPointer().name, checkedindex.internalPointer().x, checkedindex.internalPointer().y)
        #     for checkedindex
        #     in checkedindices]:
        #     for result in resultset:
        #         if xoutput.name in result and youtput.name in result:
        #             self.plot(result[xoutput.name], result[youtput.name], name=name)

        # self._auto_pen()

    def plot(self, *args, **kwargs):
        self.plotwidget.plotItem.plot(*args, **kwargs)

    def _auto_pen(self):
        count = len(self.plotwidget.scene().items())
        self.clear_legend()
        for i, item in enumerate(self.plotwidget.scene().items()):
            if isinstance(item, PlotDataItem):
                item.setPen(mkPen(intColor(i, values=count), width=2))
                self.legend.addItem(item, item.name())

    def replot_all(self, checked=True):
        if not checked: return
        self.plotwidget.clear()
        for result in self._cache.values():
            self.plot_mode(result)

    def clear_all(self):
        self.plotwidget.clear()
        self.legend.items = []
        self._cache = {}

    def clear_legend(self):
        self.legend.scene().removeItem(self.legend)
        self.legend = self.plotwidget.addLegend()

    @property
    def inputs(self):
        return super(SAXSSpectra, self).inputs()

    def sizeHint(self):
        return QSize(150, 200)


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
