from qtpy.QtWidgets import *
from qtpy.QtCore import *
from qtpy.QtGui import *
from xicam.plugins.WidgetPlugin import QWidgetPlugin
from xicam.gui.static import path


class SAXSToolbar(QToolBar, QWidgetPlugin):
    name = 'SAXSToolbar'
    sigPlotCache = Signal()
    sigDoWorkflow = Signal()

    def __init__(self, tabwidget: QTabWidget):
        super(SAXSToolbar, self).__init__()

        self.results = []

        self.tabwidget = tabwidget

        self.detectorcombobox = QComboBox()
        self.tabwidget.model.dataChanged.connect(self.updatedetectorcombobox)

        self.addWidget(self.detectorcombobox)
        self.addSeparator()
        self.modegroup = QActionGroup(self)
        self.rawaction = self.mkAction('icons/raw.png', 'Raw', checkable=True, group=self.modegroup, checked=True)
        self.addAction(self.rawaction)
        self.cakeaction = self.mkAction('icons/cake.png', 'Cake (q/chi plot)', checkable=True, group=self.modegroup)
        self.addAction(self.cakeaction)
        self.remeshaction = self.mkAction('icons/remesh.png', 'Remesh (GIWAXS)', checkable=True, group=self.modegroup)
        self.addAction(self.remeshaction)
        self.addSeparator()
        self.reductionLabel = QLabel('Reduction Mode:')
        self.addWidget(self.reductionLabel)
        self.reductionModes = QComboBox(self)
        self.addWidget(self.reductionModes)
        self.reductionModesModel = QStandardItemModel()
        self.reductionModes.setModel(self.reductionModesModel)
        self.reductionModes.currentIndexChanged.connect(self.sigPlotCache)

        self.multiplot = QAction(self)
        self.multiplot.setIcon(QIcon(str(path('icons/multiplot.png'))))
        self.multiplot.setText('Plot Series')
        self.multiplot.setCheckable(True)
        self.multiplot.triggered.connect(self.sigDoWorkflow)
        self.addAction(self.multiplot)

    def updateReductionModes(self, results):
        previousindex = self.reductionModes.currentIndex()
        self.reductionModes.currentIndexChanged.disconnect(self.sigPlotCache)
        self.reductionModesModel.clear()
        for result in results:
            for key, output in result.items():
                if 'plotx' in output.hints:
                    for xname in output.hints['plotx']:
                        name = f'{result[key].name} vs. {xname} [{result[key].parent.name}]'
                        item = QStandardItem(name)
                        item.setData((result[xname], result[key]), role=256)
                        self.reductionModesModel.appendRow(item)
        self.reductionModes.setCurrentIndex(previousindex)
        self.reductionModes.currentIndexChanged.connect(self.sigPlotCache)


    def updatedetectorcombobox(self, start, end):
        if self.tabwidget.count():
            devices = self.tabwidget.currentWidget().header.devices()
            self.detectorcombobox.clear()
            self.detectorcombobox.addItems(devices)

    def mkAction(self, iconpath: str = None, text=None, receiver=None, group=None, checkable=False, checked=False):
        actn = QAction(self)
        if iconpath: actn.setIcon(QIcon(QPixmap(str(path(iconpath)))))
        if text: actn.setText(text)
        if receiver: actn.triggered.connect(receiver)
        actn.setCheckable(checkable)
        if checked: actn.setChecked(checked)
        if group: actn.setActionGroup(group)
        return actn
