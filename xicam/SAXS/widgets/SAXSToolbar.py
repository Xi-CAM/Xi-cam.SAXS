from typing import Callable, Union
from qtpy.QtWidgets import *
from qtpy.QtCore import *
from qtpy.QtGui import *
from xicam.plugins.widgetplugin import QWidgetPlugin
from xicam.gui.static import path
from xicam.core.execution.workflow import Workflow
from xicam.plugins import ProcessingPlugin, Output
from xicam.gui.widgets.menuview import MenuView
from xicam.gui.widgets.ROI import ArcROI, LineROI, BetterPolyLineROI, RectROI, SegmentedRectROI
from xicam.plugins import Hint
from functools import partial
import pyqtgraph as pg


class SAXSToolbarBase(QToolBar):
    name = 'SAXSToolbar'
    sigPlotCache = Signal()
    sigDoWorkflow = Signal()
    sigDeviceChanged = Signal(str)

    def __init__(self, *args, **kwargs):
        super(SAXSToolbarBase, self).__init__(*args)

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
    def __init__(self, *args, view: Union[Callable, pg.ImageView] = None, workflow=None, index=-1, **kwargs):
        super(ROIs, self).__init__(*args, **kwargs)
        self.workflow = workflow
        self.view = view
        self.index = index  # Where to insert the ROIs process into the workflow (default append)
        self._scale_factor = .33

        self.arc_roi = self.mkAction('icons/roi_arc.png', 'Arc ROI', self.add_arc)
        self.addAction(self.arc_roi)
        self.horizontal_roi = self.mkAction('icons/roi_horizontal.png', 'Horizontal ROI', self.add_horizontal)
        self.addAction(self.horizontal_roi)
        self.line_roi = self.mkAction('icons/roi_line.png', 'Line ROI', self.add_line)
        self.addAction(self.line_roi)
        self.polygon_roi = self.mkAction('icons/roi_polygon.png', 'Polygon ROI', self.add_polygon)
        self.addAction(self.polygon_roi)
        self.rect_segmented_roi = self.mkAction('icons/roi_rect_segmented.png', 'Segmented Rectangular ROI',
                                                self.add_rect_segmented)
        self.addAction(self.rect_segmented_roi)
        self.rect_roi = self.mkAction('icons/roi_rect.png', 'Rectangular ROI', self.add_rect)
        self.addAction(self.rect_roi)
        self.vertical_roi = self.mkAction('icons/roi_vertical.png', 'Vertical ROI', self.add_vertical)
        self.addAction(self.vertical_roi)

        self.addSeparator()

    # TODO: scale roi's by inspecting self.view

    def _scaled_size(self):
        image_bound = self.view().imageItem.boundingRect()
        width = image_bound.width()
        height = image_bound.height()
        return width * self._scale_factor, height * self._scale_factor

    def _rect_origin(self):
        image_bound = self.view().imageItem.boundingRect()
        width = image_bound.width()
        height = image_bound.height()
        origin_x = image_bound.x() + width / 2 - width / 2 * self._scale_factor
        origin_y = image_bound.y() + height / 2 - height / 2 * self._scale_factor
        return origin_x, origin_y

    def add_roi(self, roi):
        view = self.view
        if callable(view):
            view = view()

        view.getView().addItem(roi)
        self.workflow.insertProcess(self.index, roi.process, autoconnectall=True)
        # Remove the roi process from the workflow when the roi is removed
        # TODO -- should this be in BetterROI?
        roi.sigRemoveRequested.connect(lambda roi: self.workflow.removeProcess(roi.process))

    def add_arc(self):
        self.add_roi(ArcROI(center=(0, 0), radius=.25))

    def add_horizontal(self):
        ...

    def add_line(self):
        image_bound = self.view().imageItem.boundingRect()
        width = image_bound.width()
        height = image_bound.height()
        x = image_bound.x() + width / 2 + width / 2 * self._scale_factor
        y = image_bound.y() + height / 2
        self.add_roi(LineROI(pos1=(self._rect_origin()[0], y), pos2=(x, y), width=self._scaled_size()[0]))

    def add_polygon(self):
        rect = QRectF(QPointF(*self._rect_origin()), QSizeF(*self._scaled_size()))
        points = [(point.x(), point.y()) for point in [rect.bottomLeft(),
                                                       rect.bottomRight(),
                                                       rect.topRight(),
                                                       rect.topLeft()]]
        self.add_roi(BetterPolyLineROI(points, closed=True))

    def add_rect(self):
        self.add_roi(RectROI(pos=self._rect_origin(), size=self._scaled_size()))

    def add_rect_segmented(self):
        self.add_roi(SegmentedRectROI(pos=self._rect_origin(), size=self._scaled_size()))

    def add_vertical(self):
        ...


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
