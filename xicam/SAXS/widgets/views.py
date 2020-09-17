from collections import OrderedDict
from typing import List
import sys

import pyqtgraph as pg
from pyqtgraph.graphicsItems.LegendItem import ItemSample
from qtpy.QtCore import QModelIndex, QPersistentModelIndex, QPoint, Qt, Signal, Slot, QItemSelectionModel, QRect
from qtpy.QtGui import QPen, QStandardItem, QStandardItemModel, QKeyEvent, QIcon, QPixmap
from qtpy.QtWidgets import QApplication, QAbstractItemView, QLineEdit, QListView, QTabWidget, QTreeView, QVBoxLayout, QHBoxLayout, \
                           QWidget, QStackedWidget, QGridLayout, QPushButton, QStyle, QLabel, QGraphicsView, QScrollArea, \
                           QListWidget, QFormLayout, QRadioButton, QCheckBox, QActionGroup, QToolBar, QDockWidget, QSplitter, \
                           QFrame, QTextEdit, QStyleFactory, QMainWindow

from xicam.gui.widgets.tabview import TabView
from xicam.gui.static import path
from xicam.gui.widgets.collapsiblewidget import CollapsibleWidget
from xicam.gui.widgets.imageviewmixins import CatalogView



# For some reason, LegendItem.removeItem(ref) wasn't working, so this class stores the data name
class CurveItemSample(ItemSample):
    """
    Provides a custom ItemSample for curve items (PlotItemData) in a plot.
    """
    def __init__(self, item, **kwargs):
        self.name = kwargs.get('name', '')
        super(CurveItemSample, self).__init__(item)


class CorrelationWidget(QWidget):
    """
    Widget for viewing the correlation results.

    This could be generalized into a ComboPlotView / PlotView / ComboView ...
    """
    def __init__(self, model):
        super(CorrelationWidget, self).__init__()
        self.model = model  # type: QStandardItemModel
        self.resultsList = QTreeView(self)
        self.resultsList.setHeaderHidden(True)
        self.resultsList.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.resultsList.setSelectionMode(QAbstractItemView.NoSelection)
        self.plotOpts = dict()
        self._plot = pg.PlotWidget(**self.plotOpts)
        self._legend = pg.LegendItem(offset=[-1, 1])
        self.legend.setParentItem(self._plot.getPlotItem())
        self.resultsList.setModel(self.model)
        self.selectionModel = self.resultsList.selectionModel()

        layout = QVBoxLayout()
        layout.addWidget(self.resultsList)
        layout.addWidget(self._plot)
        self.setLayout(layout)

        self.checkedItemIndexes = []
        self._curveItems = []
        # self.model.itemChanged.connect(self.updatePlot)

    def clear(self):
        raise NotImplementedError

    @property
    def plot(self):
        return self._plot

    @property
    def legend(self):
        return self._legend

    def _clearLegend(self):
        for curveItem in self._curveItems:
            self.legend.removeItem(name=curveItem.name)
        self.legend.hide()

    def results(self, dataKey):
        for index in self.checkedItemIndexes:
            yield index.data(Qt.UserRole)['data'].get(dataKey, np.array([]))

    def parentItemSet(self):
        parents = set()
        for index in self.checkedItemIndexes:
            parents.add(QPersistentModelIndex(index.parent()))
        return parents

    def updatePlot(self, item: QStandardItem):
        raise NotImplementedError


class OneTimeWidget(CorrelationWidget):
    def __init__(self, model):
        self.model = model
        if not model:
            self.model = QStandardItemModel()
        super(OneTimeWidget, self).__init__(self.model)
        plotItem = self._plot.getPlotItem()
        plotItem.setLabel('left', 'g<sub>2</sub>(&tau;)', 's')
        plotItem.setLabel('bottom', '&tau;', 's')
        plotItem.setLogMode(x=True)

    def clear(self):
        self.plot.clear()
        self._clearLegend()
        self._curveItems.clear()

    def updatePlot(self, item: QStandardItem):
        self.clear()

        itemIndex = QPersistentModelIndex(item.index())
        if item.checkState():
            self.checkedItemIndexes.append(itemIndex)
        else:
            # TODO -- might need try for ValueError
            self.checkedItemIndexes.remove(itemIndex)

        g2 = list(self.results('norm-0-g2'))
        g2Err = list(self.results('norm-0-stderr'))
        lagSteps = list(self.results('tau'))
        fitCurve = list(self.results('g2avgFIT1'))
        roiList = list(self.results('dqlist'))

        for roi in range(len(self.checkedItemIndexes)):
            yData = g2[roi].squeeze()
            xData = lagSteps[roi].squeeze()

            color = [float(roi) / len(self.checkedItemIndexes) * 255,
                     (1 - float(roi) / len(self.checkedItemIndexes)) * 255,
                     255]
            self.plotOpts['pen'] = color
            err = g2Err[roi].squeeze()
            self.plot.addItem(pg.ErrorBarItem(x=np.log10(xData), y=yData, top=err, bottom=err, **self.plotOpts))

            curve = self.plot.plot(x=xData, y=yData, **self.plotOpts)
            opts = self.plotOpts.copy()
            opts['pen'] = pg.mkPen(self.plotOpts['pen'])  # type: QPen
            opts['pen'].setStyle(Qt.DashLine)
            name = roiList[roi]
            curveItem = CurveItemSample(curve, name=name)
            self._curveItems.append(curveItem)
            self.legend.addItem(curveItem, curveItem.name)
            if len(fitCurve[roi]) > 0:
                fit_curve = self.plot.plot(x=xData, y=fitCurve[roi].squeeze(), **opts)
                fitCurveItem = CurveItemSample(fit_curve, name=f'{name} (fit)')
                self._curveItems.append(fitCurveItem)
                self.legend.addItem(fitCurveItem, fitCurveItem.name)
            self.legend.show()


class TwoTimeWidget(CorrelationWidget):
    ...


class FileSelectionView(QWidget):
    """
    Widget for viewing and selecting the loaded files.
    """
    def __init__(self, headermodel, selectionmodel):
        """

        Parameters
        ----------
        headermodel
            The model to use in the file list view
        selectionmodel
            The selection model to use in the file list view
        """
        super(FileSelectionView, self).__init__()
        # self.parameters = ParameterTree()
        self.fileListView = QListView()
        self.correlationName = QLineEdit()
        self.correlationName.setPlaceholderText('Name of result')

        layout = QVBoxLayout()
        layout.addWidget(self.fileListView)
        layout.addWidget(self.correlationName)
        self.setLayout(layout)

        self.headerModel = headermodel
        self.selectionModel = selectionmodel
        self.fileListView.setModel(headermodel)
        self.fileListView.setSelectionModel(selectionmodel)
        self.fileListView.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.fileListView.setSelectionMode(QAbstractItemView.ExtendedSelection)

        # Make sure when the tabview selection model changes, the file list
        # current item updates
        self.selectionModel.currentChanged.connect(
            lambda current, _:
                self.fileListView.setCurrentIndex(current)
        )

        self.selectionModel.currentChanged.connect(
            lambda current, _:
                self.correlationName.setPlaceholderText(current.data())
        )


class ResultsWidget(QWidget):
    
    def __init__(self, model, parent=None):
        super(ResultsWidget, self).__init__(parent)
        
        self._model = model
        self._derivedDataView = DataSelectorView()
        self._derivedDataView.setModel(self._model)
        self._hintView = ResultsTabView()
        self._hintView.setModel(self._model)

        self._derivedDataWidget = CollapsibleWidget(self._derivedDataView, "Results")
        self._derivedDataWidget.addWidget(self._hintView)
        self.setLayout(self._derivedDataWidget.layout())


_canvas_cache = {}
def canvas_from_index(index:int)-> QWidget:
    if index not in _canvas_cache:
        _canvas_cache[index] = QGraphicsView()
    return _canvas_cache[index]


# def add_static_data(self):
#     try:
#         catalog = self.catalogmodel.item(-1).data(Qt.UserRole)
#         widget2D = self.widgetcls(catalog=catalog, stream=self.stream, field=self.field)
#         return widget2D
#     except:
#         pass
#         # raise AttributeError
#         # print("No Catalog selected yet")


# helper class
# class LayoutFiller(QWidget):
#
#     def addWidget(self, widget):
#         ...
#
#     def insertWidget

class StackedResultsWidget(QWidget):
    """
    Outer Widget for viewing results in different ways using the QStackedWidget with
    several pages one for tabview and others for different split views
    """

    def __init__(
        self,
        catalogmodel: QStandardItemModel = None,
        selectionmodel: QItemSelectionModel = None,
        widgetcls=None,
        stream=None,
        field=None,
        bindings: List[tuple] = [],
        **kwargs,
    ):
        super(StackedResultsWidget, self).__init__()
        #TODO:
        # [] implement TabView so that it shows not only different scans and but also different fields
        self.catalogmodel = catalogmodel
        self.selectionmodel = selectionmodel
        self.widgetcls = widgetcls
        self.stream = stream
        self.field = field

        # create object instances of the different layout/view widgets to be used on the different pages of the stacked widget
        self.tab_view = TabView(catalogmodel, selectionmodel, widgetcls, stream, field)
        self.hor_view = SplitHorizontal(catalogmodel=catalogmodel, selectionmodel=selectionmodel, widgetcls=widgetcls)
        self.vert_view = SplitVertical(catalogmodel=catalogmodel, selectionmodel=selectionmodel, widgetcls=widgetcls)
        self.three_view = SplitThreeView(catalogmodel=catalogmodel, selectionmodel=selectionmodel, widgetcls=widgetcls)
        self.grid_view = SplitGridView(catalogmodel=catalogmodel, selectionmodel=selectionmodel, widgetcls=widgetcls)

        ### Create stacked widget and fill pages with different layout widgets
        self.stackedwidget = QStackedWidget(self)
        self.stackedwidget.addWidget(self.tab_view)
        self.stackedwidget.addWidget(self.hor_view)
        self.stackedwidget.addWidget(self.vert_view)
        self.stackedwidget.addWidget(self.three_view)
        self.stackedwidget.addWidget(self.grid_view)

        ### Create Button Panel
        # TODO make button panel look nice
        self.buttonpanel = QHBoxLayout()
        self.buttonpanel.addStretch(10)
        ### Create Buttons
        self.button_tab = QPushButton()
        self.button_tab.setIcon(QIcon(path('icons/tabs.png')))
        self.button_hor = QPushButton()
        self.button_hor.setIcon(QIcon(path('icons/1x1hor.png')))
        self.button_vert = QPushButton()
        self.button_vert.setIcon(QIcon(path('icons/1x1vert.png')))
        self.button_three = QPushButton()
        self.button_three.setIcon(QIcon(path('icons/2x1grid.png')))
        self.button_grid = QPushButton()
        self.button_grid.setIcon(QIcon(path('icons/2x2grid.png')))
        ### Add Buttons to Panel
        self.buttonpanel.addWidget(self.button_tab)
        self.buttonpanel.addWidget(self.button_hor)
        self.buttonpanel.addWidget(self.button_vert)
        self.buttonpanel.addWidget(self.button_three)
        self.buttonpanel.addWidget(self.button_grid)
        ### Connect Buttons to function
        self.button_tab.clicked.connect(self.display_tab)
        self.button_hor.clicked.connect(self.display_hor)
        self.button_vert.clicked.connect(self.display_vert)
        self.button_three.clicked.connect(self.display_three)
        self.button_grid.clicked.connect(self.display_grid)
        ### define outer layout & add stacked widget and button panel
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.stackedwidget)
        self.layout.addLayout(self.buttonpanel)
        self.setLayout(self.layout)
        self.show()

    def display_tab(self):
        self.stackedwidget.setCurrentIndex(0)

    def display_hor(self):
        canvas0 = canvas_from_index(0)
        canvas1 = canvas_from_index(1)
        self.hor_view.splitter.insertWidget(0, canvas0)
        self.hor_view.splitter.insertWidget(1, canvas1)
        self.stackedwidget.setCurrentIndex(1)

        # cur_index = self.stackedwidget.currentIndex()
        # _widget = self.stackedwidget.widget(cur_index)
        # qframes = _widget.the_widget_list
        # self.stackedwidget.setCurrentIndex(1)
        # widget = self.stackedwidget.widget(1)
        # widget.the_widget_list = qframes

    def display_vert(self):
        canvas0 = canvas_from_index(0)
        canvas1 = canvas_from_index(1)
        self.vert_view.splitter.insertWidget(0, canvas0)
        self.vert_view.splitter.insertWidget(1, canvas1)
        self.stackedwidget.setCurrentIndex(2)

    def display_three(self):
        canvas0 = canvas_from_index(0)
        canvas1 = canvas_from_index(1)
        canvas2 = canvas_from_index(2)
        self.three_view.top_splitter.insertWidget(0, canvas0)
        self.three_view.top_splitter.insertWidget(1, canvas1)
        self.three_view.outer_splitter.insertWidget(1, canvas2)
        self.stackedwidget.setCurrentIndex(3)

    def display_grid(self):
        canvas0 = canvas_from_index(0)
        canvas1 = canvas_from_index(1)
        canvas2 = canvas_from_index(2)
        canvas3 = canvas_from_index(3)
        self.grid_view.top_splitter.insertWidget(0, canvas0)
        self.grid_view.top_splitter.insertWidget(1, canvas1)
        self.grid_view.bottom_splitter.insertWidget(0, canvas2)
        self.grid_view.bottom_splitter.insertWidget(1, canvas3)
        self.stackedwidget.setCurrentIndex(4)

class SplitView(QWidget):
    """
    Displaying results in a (dynamic) split view.
    """

    def __init__(
        self,
        catalogmodel: QStandardItemModel = None,
        selectionmodel: QItemSelectionModel = None,
        widgetcls=None,
        stream=None,
        field=None,
        bindings: List[tuple] = [],
        split_mode: str = 'gridview',
        **kwargs,
    ):
        super(SplitView, self).__init__()

        self.catalogmodel = catalogmodel
        self.selectionmodel = selectionmodel
        self.widgetcls = widgetcls
        self.stream = stream
        self.field = field
        self.split_mode = split_mode

        self.layout = QHBoxLayout()


    #     if self.split_mode == 'horizontal':
    #         self.horizontal_split()
    #     if self.split_mode == 'vertical':
    #         self.vertical_split()
    #     if self.split_mode == 'threeview':
    #         self.threeview_split()
    #     if self.split_mode == 'gridview':
    #         self.grid()
    #
    #
    # def horizontal_split(self):
    #
    #     top.setFrameShape(QFrame.StyledPanel)
    #     bottom.setFrameShape(QFrame.StyledPanel)
    #
    #     splitter = QSplitter(Qt.Vertical)
    #     splitter.addWidget(top)
    #     splitter.addWidget(bottom)
    #     splitter.setSizes([100, 200])
    #
    #     hbox.addWidget(splitter)
    #     self.setLayout(hbox)
    #     # QApplication.setStyle(QStyleFactory.create('Cleanlooks'))
    #     self.setGeometry(300, 300, 300, 200)
    #
    # def vertical_split(self):
    #     hbox = QHBoxLayout(self)
    #     left = QFrame()
    #     right = QFrame()
    #     left.setFrameShape(QFrame.StyledPanel)
    #     right.setFrameShape(QFrame.StyledPanel)
    #
    #     splitter = QSplitter(Qt.Horizontal)
    #     splitter.addWidget(left)
    #     splitter.addWidget(right)
    #     splitter.setSizes([100, 200])
    #
    #     hbox.addWidget(splitter)
    #     self.setLayout(hbox)
    #     # QApplication.setStyle(QStyleFactory.create('Cleanlooks'))
    #     self.setGeometry(300, 300, 300, 200)
    #
    # def threeview_split(self):
    #     hbox = QHBoxLayout(self)
    #
    #     topleft = QFrame()
    #     topright = QFrame()
    #     topleft.setFrameShape(QFrame.StyledPanel)
    #     topright.setFrameShape(QFrame.StyledPanel)
    #     bottom = QFrame()
    #     bottom.setFrameShape(QFrame.StyledPanel)
    #
    #     splitter1 = QSplitter(Qt.Horizontal)
    #     splitter1.addWidget(topleft)
    #     splitter1.addWidget(topright)
    #     splitter1.setSizes([100, 200])
    #
    #     splitter2 = QSplitter(Qt.Vertical)
    #     splitter2.addWidget(splitter1)
    #     splitter2.addWidget(bottom)
    #
    #     hbox.addWidget(splitter2)
    #     self.setLayout(hbox)
    #     # QApplication.setStyle(QStyleFactory.create('Cleanlooks'))
    #     self.setGeometry(300, 300, 300, 200)
    #     self.show()
    #
    # def grid(self):
    #     hbox = QVBoxLayout(self)
    #
    #     topleft = QFrame()
    #     topright = QFrame()
    #     topleft.setFrameShape(QFrame.StyledPanel)
    #     topright.setFrameShape(QFrame.StyledPanel)
    #     bottomleft = QFrame()
    #     bottomright = QFrame()
    #     bottomleft.setFrameShape(QFrame.StyledPanel)
    #     bottomright.setFrameShape(QFrame.StyledPanel)
    #
    #     splitter1 = QSplitter(Qt.Horizontal)
    #     splitter1.addWidget(topleft)
    #     splitter1.addWidget(topright)
    #     splitter1.setSizes([100, 200])
    #
    #     splitter2 = QSplitter(Qt.Horizontal)
    #     splitter2.addWidget(bottomleft)
    #     splitter2.addWidget(bottomright)
    #     splitter2.setSizes([100, 200])
    #
    #     # connect splitter1 and splitter2 to move together
    #     # TODO which version is desired? connect splitter or free moving?
    #     splitter1.splitterMoved.connect(self.moveSplitter)
    #     splitter2.splitterMoved.connect(self.moveSplitter)
    #     self._spltA = splitter1
    #     self._spltB = splitter2
    #
    #     outer_splitter = QSplitter(Qt.Vertical)
    #     outer_splitter.addWidget(splitter1)
    #     outer_splitter.addWidget(splitter2)
    #     outer_splitter.setSizes([200, 400])
    #
    #     hbox.addWidget(outer_splitter)
    #     self.setLayout(hbox)
    #     # QApplication.setStyle(QStyleFactory.create('Cleanlooks'))
    #     self.setGeometry(300, 300, 300, 200)
    #     self.show()
    #
    # def update_view(self):
    #     available_widgets = self.gridLayout.rowCount() * self.gridLayout.columnCount()
    #     for i in range(self.catalogmodel.rowCount()):
    #         if i > available_widgets - 1 :
    #             return
    #         itemdata = self.catalogmodel.item(i).data(Qt.UserRole)
    #         # TODO: use projection from catalog data to figure this out
    #         widget = QLabel(self.catalogmodel.item(i).data(Qt.DisplayRole)) # temporary
    #
    # def add_static_data(self):
    #     try:
    #         catalog = self.catalogmodel.item(-1).data(Qt.UserRole)
    #         widget2D = self.widgetcls(catalog=catalog, stream=self.stream, field=self.field)
    #         return widget2D
    #     except:
    #         pass
    #         # raise AttributeError
    #         # print("No Catalog selected yet")
    #
    # def add_data(self):
    #     selected_indexes = [self.catalogmodel.item(i) for i in range(self.catalogmodel.rowCount())]
    #     # TODO ensemblemodel will replace catalog or selectionmodel
    #     widgets = []
    #     for index in selected_indexes:
    #         # data = catalog_run.primary.to_dask()['fccd_image']
    #         catalog_run = index.data(Qt.UserRole)
    #         catalog_label = index.data(Qt.DisplayRole)
    #         widget2D = self.widgetcls(catalog=catalog_run, stream=self.stream, field=self.field)
    #         widgets.append(widget2D)
    #     return widgets

    # TODO [ ] add note/hint if to few/many dataset selected
    #      [ ] label dataset in view
    #      [ ] add widgetcls to all option --> automatic filling
    #      [ ] get 1d plot results to show --> need dataset for testing
    #      [ ] automatic update view when more data is selected

class SplitHorizontal(SplitView):
    """ Displays data in wide view, 2 on top of each other with a horizontal, movable divider bar"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.splitter = QSplitter(Qt.Vertical)
        self.splitter.setSizes([100, 200])

        self.layout.addWidget(self.splitter)
        self.setLayout(self.layout)
        QApplication.setStyle(QStyleFactory.create('Cleanlooks'))
        self.setGeometry(300, 300, 300, 200)
        self.show()


class SplitVertical(SplitView):
    """ Displays data in vertical view, 2 next to each other with a vertical, movable divider bar"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setSizes([100, 200])

        self.layout.addWidget(self.splitter)
        self.setLayout(self.layout)
        QApplication.setStyle(QStyleFactory.create('Cleanlooks'))
        self.setGeometry(300, 300, 300, 200)
        self.show()


class SplitThreeView(SplitView):
    """ Shows 3 data displays: 2 next to each other with a vertical, movable divider bar
        and a third one below these in wide view with a horizontal, movable divider bar
    """
    def __init__(self, *args, **kwargs):
        super(SplitThreeView, self).__init__(*args, **kwargs)

        self.top_splitter = QSplitter(Qt.Horizontal)
        self.top_splitter.setSizes([100, 200])

        self.outer_splitter = QSplitter(Qt.Vertical)
        self.outer_splitter.insertWidget(0, self.top_splitter)

        self.layout.addWidget(self.outer_splitter)
        self.setLayout(self.layout)
        QApplication.setStyle(QStyleFactory.create('Cleanlooks'))
        self.setGeometry(300, 300, 300, 200)
        self.show()


class SplitGridView(SplitView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.top_splitter = QSplitter(Qt.Horizontal)
        self.top_splitter.setSizes([100, 200])

        self.bottom_splitter = QSplitter(Qt.Horizontal)
        self.bottom_splitter.setSizes([100, 200])

        # connect splitter1 and splitter2 to move together
        # TODO which version is desired? connect splitter or free moving?
        self.top_splitter.splitterMoved.connect(self.moveSplitter)
        self.bottom_splitter.splitterMoved.connect(self.moveSplitter)
        self._spltA = self.top_splitter
        self._spltB = self.bottom_splitter

        self.outer_splitter = QSplitter(Qt.Vertical)
        self.outer_splitter.insertWidget(0, self.top_splitter)
        self.outer_splitter.insertWidget(1, self.bottom_splitter)
        self.outer_splitter.setSizes([200, 400])

        self.layout.addWidget(self.outer_splitter)
        self.setLayout(self.layout)
        QApplication.setStyle(QStyleFactory.create('Cleanlooks'))
        self.setGeometry(300, 300, 300, 200)
        self.show()

    def moveSplitter( self, index, pos):
        splt = self._spltA if self.sender() == self._spltB else self._spltB
        splt.blockSignals(True)
        splt.moveSplitter(index, pos)
        splt.blockSignals(False)


def main():
    app = QApplication(sys.argv)
    ex = StackedResultsWidget()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()


class DerivedDataWidgetTestClass(QWidget):
    """
    Widget for viewing derived data. This widget contains two widgets: a collapsible one and a non-collapsible one.
    The collapsible widget can be collapsed/uncollapsed by clicking a tool button. The non-collapsible widget always
    remains visible in the widget.
    """

    def __init__(self, collapseView, staticView, parent=None):
        """

        Parameters
        ----------
        collapseView
            View/widget that becomes collapsible
        staticView
            View/widget that does not collapse
        parent
            Parent Qt widget
        """
        super(DerivedDataWidgetTestClass, self).__init__(parent)

        self.collapseWidget = CollapsibleWidget(collapseView, "Results")
        self.staticView = staticView

        self.collapseWidget.addWidget(staticView)
        self.setLayout(self.collapseWidget.layout())


class ResultsTabView(QAbstractItemView):
    """
    View that is responsible for displaying Hints in a tab-based manner.
    """

    def __init__(self, parent=None):
        super(ResultsTabView, self).__init__(parent)

        self._tabWidget = QTabWidget()
        self._tabWidget.setParent(self)
        self._indexToTabMap = OrderedDict()

        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().addWidget(self._tabWidget)

    def _findTab(self, tabName):
        """
        Convenience function to find a tab by name (instead of by index as provide by Qt's API).

        Parameters
        ----------
        tabName
            Name of the tab to attempt to find.

        Returns
        -------
        QWidget
            If found, returns the found widget with name ``tabName``. Raises an IndexError if not found.

        """
        for i in range(self._tabWidget.count()):
            if self._tabWidget.tabText(i) == tabName:
                return self._tabWidget.widget(i)
        raise IndexError

    def dataChanged(self, topLeft: QModelIndex, bottomRight: QModelIndex, roles=None):
        """
        Re-implements the QAbstractItemView.dataChanged() slot.

        When the data attached to the Qt.CheckStateRole has been changed, this will either render a Hint or remove the
        Hint visualization.

        Parameters
        ----------
        topLeft
            For now, the only index we are concerned with, which corresponds to the item's check state changing.
        bottomRight
            (Unused right now)
        roles
            List of roles attached to the data state change.

        """
        if roles is None:
            roles = []
        if self.model():
            # empty list indicates ALL roles have changed (see documentation)
            if Qt.CheckStateRole in roles or len(roles) == 0:
                hint = topLeft.data(Qt.UserRole)
                if hint:
                    if topLeft.data(Qt.CheckStateRole) == Qt.Checked:
                        if hint.group not in [self._tabWidget.tabText(index) for index in range(self._tabWidget.count())]:
                            canvas = hint.init_canvas(addLegend=True)
                            self._tabWidget.addTab(canvas, hint.group)
                        else:
                            canvas = self._findTab(hint.group)
                        hint.visualize(canvas)
                    else:
                        hint.remove()
            super(ResultsTabView, self).dataChanged(topLeft, bottomRight, roles)

    def horizontalOffset(self):
        return 0

    def indexAt(self, point: QPoint):
        return QModelIndex()

    def moveCursor(self, QAbstractItemView_CursorAction, Union, Qt_KeyboardModifiers=None, Qt_KeyboardModifier=None):
        return QModelIndex()

    def rowsInserted(self, index: QModelIndex, start, end):
        return

    def rowsAboutToBeRemoved(self, index: QModelIndex, start, end):
        return

    def scrollTo(self, QModelIndex, hint=None):
        return

    def verticalOffset(self):
        return 0

    def visualRect(self, QModelIndex):
        from qtpy.QtCore import QRect
        return QRect()


class DataSelectorView(QTreeView):
    # TODO -- this could probably be moved into a more generic class, e.g. CheckableTreeView
    """
    Tree view responsible for selecting which derived data to visualize.

    This view implements a checkable tree view, whereby the top-level nodes (ignoring the implicit root node) can be
    checked or unchecked to toggle the check state of all of their children nodes. Additionally, if only some of the
    children nodes are checked, the parent node will be partially checked.
    """

    def __init__(self, parent=None):
        super(DataSelectorView, self).__init__(parent)

        self.setHeaderHidden(True)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionMode(QAbstractItemView.NoSelection)
        self.setExpandsOnDoubleClick(False)

        # This was difficult to accomplish with a selection model (i.e. selectionChanged), as it created circular
        # signal emissions with dataChanged. So, we use the clicked signal to toggle checkState.
        self.clicked.connect(self.resolveChecks)

    def keyPressEvent(self, event: QKeyEvent):
        # We want to ignore any key press events for now
        event.accept()

    def resolveChecks(self, index: QModelIndex):
        """
        Logic that controls how a clicked item and children items are checked and unchecked.

        When the clicked item is checked or unchecked (and when any children need to be checked or unchecked), this
        implicitly emits the itemChanged() signal (since the Qt.CheckStatRole data is changed). This is captured by
        the HintTabView to visualize and remove Hints as appropriate.

        Parameters
        ----------
        index
            The index of the item that was clicked.
        """

        if not self.model():
            return

        item = self.model().itemFromIndex(index)
        # The item has been clicked and its previous state is unchecked (going to be checking items)
        if item.data(Qt.CheckStateRole) == Qt.Unchecked:
            # TODO: Potential duplicate signal emissions (dataChanged on setCheckState())
            if item.isCheckable():
                # First, check the clicked item
                item.setCheckState(Qt.Checked)

            # All children should be checked if the clicked item is a parent item
            if self.model().hasChildren(index):
                numChildren = self.model().rowCount(index)
                childrenIndexes = [self.model().index(row, 0, index) for row in range(numChildren)]
                for childIndex in childrenIndexes:
                    childItem = self.model().itemFromIndex(childIndex)
                    if childItem.isCheckable():
                        childItem.setCheckState(Qt.Checked)
            else: # Item is a child item
                parentIndex = index.parent()
                numChildren = self.model().rowCount(parentIndex)
                childrenIndexes = [self.model().index(row, 0, parentIndex) for row in range(numChildren)]
                # When all other siblings are already checked, update parent item to be checked as well
                if all([self.model().itemFromIndex(index).checkState() == Qt.Checked for index in childrenIndexes]):
                    self.model().itemFromIndex(parentIndex).setCheckState(Qt.Checked)
                else: # Not all siblings are checked, indicate with parent item being partially checked
                    self.model().itemFromIndex(parentIndex).setCheckState(Qt.PartiallyChecked)

        else: # The item has been clicked and its previous state is checked (going to be unchecking items)
            if item.isCheckable():
                # First, uncheck the clicked item
                item.setCheckState(Qt.Unchecked)

            # All children should be unchecked if the clicked item is a parent item
            if self.model().hasChildren(index):
                if self.model().itemFromIndex(index).checkState() == Qt.PartiallyChecked:
                    raise NotImplementedError
                numChildren = self.model().rowCount(index)
                childrenIndexes = [self.model().index(row, 0, index) for row in range(numChildren)]
                for childIndex in childrenIndexes:
                    childItem = self.model().itemFromIndex(childIndex)
                    if childItem.isCheckable():
                        childItem.setCheckState(Qt.Unchecked)
            else:  # The clicked item is a child item
                parentIndex = index.parent()
                numChildren = self.model().rowCount(parentIndex)
                childrenIndexes = [self.model().index(row, 0, parentIndex) for row in range(numChildren)]
                # If any other sibling is unchecked, partially check the parent item
                if any([self.model().itemFromIndex(index).checkState() == Qt.Checked for index in childrenIndexes]):
                    self.model().itemFromIndex(parentIndex).setCheckState(Qt.PartiallyChecked)
                else: # No other siblings are checked, so uncheck the parent item
                    self.model().itemFromIndex(parentIndex).setCheckState(Qt.Unchecked)


class CatalogModel(QStandardItemModel):
    """
    Derived data model that disables user interaction with the items.

    This is done so the DerivedDataView can listen for clicked signals and then control the checking logic.
    Using the Qt.ItemIsEnabled flag prevents the user from direcly checking / unchecking the item.
    """
    def __init__(self):
        super(CatalogModel, self).__init__()

    def flags(self, index: QModelIndex):
        if not index.isValid():
            return None
        if index.column() == 0:
            flags = Qt.ItemIsEnabled
        else:
            flags = super(CatalogModel, self).flags(index)
        return flags


# if __name__ == "__main__":
#     from qtpy.QtWidgets import QApplication, QMainWindow, QAction
#     app = QApplication([])
#
#     window = QMainWindow()
#     layout = QVBoxLayout()
#     model = CatalogModel()
#
#     from xicam.plugins.hints import PlotHint, ImageHint, CoPlotHint
#     parentItem = QStandardItem("blah")
#     parentItem.setCheckable(True)
#     import numpy as np
#     for i in range(3):
#         hint = PlotHint(np.arange(10), np.random.random((10,)), name=f"1-Time")
#         item = QStandardItem(hint.group)
#         item.setData(hint, Qt.UserRole)
#         item.setCheckable(True)
#         parentItem.appendRow(item)
#     hint = ImageHint(np.random.random((100,100)), xlabel="x", ylabel="y", name="2-Time")
#     item = QStandardItem(hint.group)
#     item.setData(hint, Qt.UserRole)
#     item.setCheckable(True)
#     parentItem.appendRow(item)
#     model.appendRow(parentItem)
#
#     workflowItem = QStandardItem("A Workflow Result")
#     workflowItem.setCheckable(True)
#     hints = []
#     for i in range(2):
#         if i == 0:
#             style = Qt.SolidLine
#         else:
#             style = Qt.DashLine
#         hint = PlotHint(np.arange(10), np.random.random((10,)), name=f"plot{i}", style=style)
#         hints.append(hint)
#     coplothint = CoPlotHint(*hints, name="COPLOT")
#     coPlotItem = QStandardItem(coplothint.name)
#     coPlotItem.setCheckable(True)
#     coPlotItem.setData(coplothint, Qt.UserRole)
#     workflowItem.appendRow(coPlotItem)
#     model.appendRow(workflowItem)
#
#     workflowItem = QStandardItem("A Workflow Result")
#     workflowItem.setCheckable(True)
#     hints = []
#     for i in range(2):
#         if i == 0:
#             style = Qt.SolidLine
#         else:
#             style = Qt.DashLine
#         hint = PlotHint(np.arange(10), np.random.random((10,)), name=f"plot{i}", style=style)
#         hints.append(hint)
#     coplothint = CoPlotHint(*hints, name="COPLOT")
#     coPlotItem = QStandardItem(coplothint.name)
#     coPlotItem.setCheckable(True)
#     coPlotItem.setData(coplothint, Qt.UserRole)
#     workflowItem.appendRow(coPlotItem)
#     model.appendRow(workflowItem)
#
#     lview = DataSelectorView()
#     lview.setModel(model)
#     rview = ResultsTabView()
#     rview.setModel(model)
#
#     widget = DerivedDataWidgetTestClass(lview, rview)
#
#     window.setCentralWidget(widget)
#     window.show()
#
#     app.exec()


# def main():
#     app = QApplication([])
#     window = SplitHorizontal(QLabel('Test'))
#     window.show()
#     sys.exit(app.exec_())
#
#
# if __name__ == '__main__':
#     main()