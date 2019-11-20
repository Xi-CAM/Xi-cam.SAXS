from qtpy.QtWidgets import *
from qtpy.QtCore import *
from qtpy.QtGui import *
from xicam.plugins.widgetplugin import QWidgetPlugin
from xicam.gui.static import path
from xicam.core.execution.workflow import Workflow
from xicam.plugins import ProcessingPlugin, Output
from xicam.gui.widgets.menuview import MenuView
from xicam.gui.widgets.ROI import ArcROI
from xicam.plugins import Hint
from functools import partial
import pyqtgraph as pg


class SAXSToolbarBase(QToolBar):
    name = 'SAXSToolbar'
    sigPlotCache = Signal()
    sigDoWorkflow = Signal()
    sigDeviceChanged = Signal(str)

    def __init__(self, *args, **kwargs):
        super(SAXSToolbarBase, self).__init__()

    def mkAction(self, iconpath: str = None, text=None, receiver=None, group=None, checkable=False, checked=False):
        actn = QAction(self)
        if iconpath: actn.setIcon(QIcon(QPixmap(str(path(iconpath)))))
        if text: actn.setText(text)
        if receiver: actn.triggered.connect(receiver)
        actn.setCheckable(checkable)
        if checked: actn.setChecked(checked)
        if group: actn.setActionGroup(group)
        return actn


class FieldSelector(SAXSToolbarBase):

    def __init__(self, headermodel: QStandardItemModel, selectionmodel: QItemSelectionModel, *args, **kwargs):
        self.headermodel = headermodel
        self.selectionmodel = selectionmodel
        self.headermodel.dataChanged.connect(self.updatedetectorcombobox)

        super(FieldSelector, self).__init__()

        self.detectorcombobox = QComboBox()
        self.addWidget(self.detectorcombobox)
        self.addSeparator()
        self.detectorcombobox.currentTextChanged.connect(self.sigDeviceChanged)

    def updatedetectorcombobox(self, start, end):
        if self.headermodel.rowCount():
            # TODO-- remove hard-coding of stream
            stream = "primary"
            item = self.headermodel.item(self.selectionmodel.currentIndex().row())
            # fields = getattr(item.data(Qt.UserRole), stream).to_dask().keys()
            catalog = item.data(Qt.UserRole)  # type: Catalog
            fields = [ technique["data_mapping"]["data_image"][1] for technique in catalog.metadata["techniques"] if technique["technique"] == "scattering" ]
            self.detectorcombobox.clear()
            self.detectorcombobox.addItems(fields)

class ModeSelector(SAXSToolbarBase):
    def __init__(self, *args, **kwargs):
        super(ModeSelector, self).__init__(*args, **kwargs)
        self.modegroup = QActionGroup(self)
        self.rawaction = self.mkAction('icons/raw.png', 'Raw', checkable=True, group=self.modegroup, checked=True)
        self.addAction(self.rawaction)
        self.cakeaction = self.mkAction('icons/cake.png', 'Cake (q/chi plot)', checkable=True, group=self.modegroup)
        self.addAction(self.cakeaction)
        self.remeshaction = self.mkAction('icons/remesh.png', 'Wrap Ewald Sphere', checkable=True, group=self.modegroup)
        self.addAction(self.remeshaction)
        self.addSeparator()


class MultiPlot(SAXSToolbarBase):
    def __init__(self, *args, **kwargs):
        super(MultiPlot, self).__init__(*args, **kwargs)
        self.multiplot = QAction(self)
        self.multiplot.setIcon(QIcon(str(path('icons/multiplot.png'))))
        self.multiplot.setText('Plot Series')
        self.multiplot.setCheckable(True)
        self.multiplot.triggered.connect(self.sigDoWorkflow)
        self.addAction(self.multiplot)
        self.addSeparator()


class ROIs(SAXSToolbarBase):
    def __init__(self, *args, view: pg.ImageView = None, workflow=None, **kwargs):
        super(ROIs, self).__init__(*args, **kwargs)
        self.workflow = workflow
        self.view = view

        self.arc_roi = self.mkAction('icons/roi_arc.png', 'Arc ROI')
        self.addAction(self.arc_roi)
        self.polygon_roi = self.mkAction('icons/roi_polygon.png', 'Polygon ROI')
        self.addAction(self.polygon_roi)
        self.horizontal_roi = self.mkAction('icons/roi_horizontal.png', 'Horizontal ROI')
        self.addAction(self.horizontal_roi)
        self.vertical_roi = self.mkAction('icons/roi_vertical.png', 'Vertical ROI')
        self.addAction(self.vertical_roi)
        self.line_roi = self.mkAction('icons/roi_line.png', 'Line ROI')
        self.addAction(self.line_roi)

        self.addSeparator()

        self.arc_roi.triggered.connect(self.add_arc)

    def add_arc(self):
        self.add_roi(ArcROI(center=(0, 0), radius=.25))

    def add_roi(self, roi):
        view = self.view
        if callable(view):
            view = view()

        view.getView().addItem(roi)
        self.workflow.addProcess(roi.process)



class SAXSToolbarRaw(FieldSelector):
    pass


class SAXSToolbarMask(FieldSelector):
    pass


class SAXSToolbarReduce(MultiPlot, ROIs, ModeSelector, FieldSelector):
    def __init__(self, *args, **kwargs):
        super(SAXSToolbarReduce, self).__init__(*args, **kwargs)


class CheckableWorkflowOutputModel(QAbstractItemModel):
    def __init__(self, workflow: Workflow, *args):
        super(CheckableWorkflowOutputModel, self).__init__(*args)
        self.workflow = workflow
        self.workflow.attach(partial(self.modelReset.emit))

    def index(self, row, column, parent=None):
        if parent is None or not parent.isValid():
            if row > len(self.workflow.processes) - 1: return QModelIndex()
            return self.createIndex(row, column, self.workflow.processes[row])

        parentNode = parent.internalPointer()

        if isinstance(parentNode, ProcessingPlugin):
            return self.createIndex(row, column, parentNode.hints[row])
        return QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()
        node = index.internalPointer()
        if isinstance(node, ProcessingPlugin):
            return QModelIndex()
        if isinstance(node, Hint):
            if node.parent not in self.workflow.processes: return QModelIndex()
            return self.createIndex(self.workflow.processes.index(node.parent), 0, node.parent)

        return QModelIndex()

    def rowCount(self, parent=None, *args, **kwargs):

        if parent is None or not parent.isValid():
            return len(self.workflow.processes)

        node = parent.internalPointer()
        if isinstance(node, ProcessingPlugin):
            return len(node.hints)

        return 0

    def columnCount(self, parent=None, *args, **kwargs):
        return 1

    def data(self, index: QModelIndex, role):
        if role == Qt.DisplayRole:
            return index.internalPointer().name
        elif role == Qt.CheckStateRole and isinstance(index.internalPointer(), Hint):
            return index.internalPointer().checked

    def setData(self, index: QModelIndex, value, role=Qt.EditRole):
        if role == Qt.CheckStateRole:
            index.internalPointer().checked = value

    def flags(self, index):
        if index.parent().isValid():  # if index is a hint
            return Qt.ItemIsUserCheckable | Qt.ItemIsSelectable | Qt.ItemIsEnabled
        elif index.internalPointer().hints:  # if index is a process with hints
            return Qt.ItemIsEnabled
        else:
            return

    def checkedIndices(self):
        return [self.index(hintindex, 0, self.index(procindex, 0))
                for procindex in range(self.rowCount())
                for hintindex in range(self.rowCount(self.index(procindex, 0)))
                if self.data(self.index(hintindex, 0, self.index(procindex, 0)), Qt.CheckStateRole)]
