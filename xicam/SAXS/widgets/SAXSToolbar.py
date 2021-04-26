from typing import Callable, Union
from qtpy.QtWidgets import *
from qtpy.QtCore import *
from qtpy.QtGui import *
from xicam.plugins.widgetplugin import QWidgetPlugin
from xicam.gui.static import path
from xicam.core.execution.workflow import Workflow
from xicam.plugins import OperationPlugin
from xicam.gui.widgets.menuview import MenuView
from xicam.gui.widgets.ROI import ArcROI, LineROI, BetterPolyLineROI, BetterRectROI, SegmentedRectROI
from xicam.core import msg
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

        self.addWidget(QLabel("Detector: "))
        self.detectorcombobox = QComboBox()
        self.detectorcombobox.setSizeAdjustPolicy(QComboBox.AdjustToContents)
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

# TODO maybe toolbar is not the best solution here, instead having the buttonbox in the compare stage
# class ResultsModeSelector(SAXSToolbarBase):
#     def __init__(self, *args, **kwargs):
#         super(ResultsModeSelector, self).__init__(*args, **kwargs)
#         self.viewmodegroup = QActionGroup(self)
#         self.tabmode = self.mkAction(iconpath='icons/tabs.png', text='Tab View', checkable=True, group=self.viewmodegroup, checked=True)
#         self.addAction(self.tabmode)
#         self.gridmode = self.mkAction(iconpath='icons/grid.png', text='Grid View', checkable=True, group=self.viewmodegroup)
#         self.addAction(self.gridmode)
#         self.addSeparator()


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

        self.roi_button = QToolButton()
        self.roi_button.setText("Create ROI")
        self.roi_button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.roi_button.setPopupMode(QToolButton.InstantPopup)
        self.roi_menu = QMenu()
        self.roi_button.setMenu(self.roi_menu)
        # TODO -- disable button until we have loaded data

        self.arc_roi = self.mkAction('icons/roi_arc.png', 'Arc ROI', self.add_arc)
        self.roi_menu.addAction(self.arc_roi)
        # self.horizontal_roi = self.mkAction('icons/roi_horizontal.png', 'Horizontal ROI', self.add_horizontal)
        # self.roi_menu.addAction(self.horizontal_roi)
        self.line_roi = self.mkAction('icons/roi_line.png', 'Line ROI', self.add_line)
        self.roi_menu.addAction(self.line_roi)
        self.polygon_roi = self.mkAction('icons/roi_polygon.png', 'Polygon ROI', self.add_polygon)
        self.roi_menu.addAction(self.polygon_roi)
        self.rect_segmented_roi = self.mkAction('icons/roi_rect_segmented.png', 'Segmented Rectangular ROI',
                                                self.add_rect_segmented)
        self.roi_menu.addAction(self.rect_segmented_roi)
        self.rect_roi = self.mkAction('icons/roi_rect.png', 'Rectangular ROI', self.add_rect)
        self.roi_menu.addAction(self.rect_roi)
        # self.vertical_roi = self.mkAction('icons/roi_vertical.png', 'Vertical ROI', self.add_vertical)
        # self.roi_menu.addAction(self.vertical_roi)

        self.addWidget(self.roi_button)

        self.addSeparator()

    # TODO: scale roi's by inspecting self.view

    def _get_view(self):
        view = self.view
        if callable(view):
            view = view()
        return view

    def _scaled_size(self):
        view = self._get_view()
        if view:
            image_bound = view.imageItem.boundingRect()
            width = image_bound.width()
            height = image_bound.height()
            return width * self._scale_factor, height * self._scale_factor
        return -1, -1

    def _rect_origin(self):
        view = self._get_view()
        if view:
            image_bound = view.imageItem.boundingRect()
            width = image_bound.width()
            height = image_bound.height()
            origin_x = image_bound.x() + width / 2 - width / 2 * self._scale_factor
            origin_y = image_bound.y() + height / 2 - height / 2 * self._scale_factor
            return origin_x, origin_y
        return -1, -1

    def add_roi(self, roi):
        view = self._get_view()
        if view:
            view.getView().addItem(roi)
            self.workflow.insert_operation(self.index, roi.operation)
            # Remove the roi process from the workflow when the roi is removed
            # TODO -- should this be in BetterROI?
            roi.sigRemoveRequested.connect(lambda roi: self.workflow.remove_operation(roi.operation))
        else:
            msg.notifyMessage("Please open an image before creating an ROI.", level=msg.WARNING)

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
        self.add_roi(BetterRectROI(pos=self._rect_origin(), size=self._scaled_size()))

    def add_rect_segmented(self):
        self.add_roi(SegmentedRectROI(pos=self._rect_origin(), size=self._scaled_size()))

    def add_vertical(self):
        ...


class SAXSToolbarRaw(FieldSelector):
    pass


class SAXSToolbarMask(FieldSelector):
    pass


class SAXSToolbarReduce(MultiPlot, ROIs, ModeSelector):
    def __init__(self, *args, **kwargs):
        super(SAXSToolbarReduce, self).__init__(*args, **kwargs)


# class  SAXSToolbarCompare(ResultsModeSelector):
#     pass

