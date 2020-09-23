from typing import List
import sys


from qtpy.QtCore import QModelIndex, QPoint, Qt, QItemSelectionModel, \
                        QItemSelection
from qtpy.QtGui import QStandardItemModel, QIcon
from qtpy.QtWidgets import QApplication, QAbstractItemView, QTabWidget, QTreeView, QVBoxLayout, QHBoxLayout, \
                           QWidget, QStackedWidget,  QPushButton,  QGraphicsView, QSplitter, QStyleFactory
from xicam.XPCS.models import XicamCanvasManager, EnsembleModel

from xicam.gui.widgets.tabview import TabView
from xicam.gui.static import path





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
from xicam.plugins.intentcanvasplugin import IntentCanvas


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


    def get_data(self):
        selected_indexes = [self.catalogmodel.item(i) for i in range(self.catalogmodel.rowCount())]
        widgets = []
        for index in selected_indexes:
            # data = catalog_run.primary.to_dask()['fccd_image']
            catalog_run = index.data(Qt.UserRole)
            catalog_label = index.data(Qt.DisplayRole)
            widget2D = self.widgetcls(catalog=catalog_run, stream=self.stream, field=self.field)
            widgets.append(widget2D)
        return widgets

    _canvas_cache = {}

    def canvas_from_index(self,index: int) -> QWidget:
        if index not in self._canvas_cache:
            self._canvas_cache[index] = QGraphicsView()
        return self._canvas_cache[index]

    def display_hor(self):
        # canvas0 = canvas_from_index(0)
        # canvas1 = canvas_from_index(1)
        canvas0 = self.get_data()[0]
        canvas1 = self.get_data()[1]
        if self.hor_view.splitter.count() == 0:
            self.hor_view.splitter.insertWidget(0, canvas0)
            self.hor_view.splitter.insertWidget(1, canvas1)
        elif self.hor_view.splitter.count() >= 2:
            pass
        self.stackedwidget.setCurrentIndex(1)

        # cur_index = self.stackedwidget.currentIndex()
        # _widget = self.stackedwidget.widget(cur_index)
        # qframes = _widget.the_widget_list
        # self.stackedwidget.setCurrentIndex(1)
        # widget = self.stackedwidget.widget(1)
        # widget.the_widget_list = qframes

    def display_vert(self):
        # canvas0 = canvas_from_index(0)
        # canvas1 = canvas_from_index(1)
        canvas0 = self.get_data()[0]
        canvas1 = self.get_data()[1]
        if self.vert_view.splitter.count() == 0:
            self.vert_view.splitter.insertWidget(0, canvas0)
            self.vert_view.splitter.insertWidget(1, canvas1)
        elif self.vert_view.splitter.count() >= 2:
            pass
        self.stackedwidget.setCurrentIndex(2)

    def display_three(self):
        # canvas0 = canvas_from_index(0)
        # canvas1 = canvas_from_index(1)
        # canvas2 = canvas_from_index(2)
        canvas0 = self.get_data()[0]
        canvas1 = self.get_data()[1]
        canvas2 = self.get_data()[2]
        if self.three_view.top_splitter.count() == 0:
            self.three_view.top_splitter.insertWidget(0, canvas0)
            self.three_view.top_splitter.insertWidget(1, canvas1)
            self.three_view.outer_splitter.insertWidget(1, canvas2)
        elif self.three_view.top_splitter.count() >= 2 and self.three_view.outer_splitter.count() >=2:
            pass
        self.stackedwidget.setCurrentIndex(3)

    def display_grid(self):
        # canvas0 = canvas_from_index(0)
        # canvas1 = canvas_from_index(1)
        # canvas2 = canvas_from_index(2)
        # canvas3 = canvas_from_index(3)
        canvas0 = self.get_data()[0]
        canvas1 = self.get_data()[1]
        canvas2 = self.get_data()[2]
        canvas3 = self.get_data()[3]
        if self.grid_view.top_splitter.count() == 0:
            self.grid_view.top_splitter.insertWidget(0, canvas0)
            self.grid_view.top_splitter.insertWidget(1, canvas1)
            self.grid_view.bottom_splitter.insertWidget(0, canvas2)
            self.grid_view.bottom_splitter.insertWidget(1, canvas3)
        elif self.grid_view.top_splitter.count() >= 2 and self.grid_view.bottom_splitter.count() >=2:
            pass
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
        # self.top_splitter.splitterMoved.connect(self.moveSplitter)
        # self.bottom_splitter.splitterMoved.connect(self.moveSplitter)
        # self._spltA = self.top_splitter
        # self._spltB = self.bottom_splitter

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

# A CanvasView
# TODO: this should be a parent class (CanvasView) that ResultsTabView and ResultsSplitView inherit from
class ResultsTabView(QAbstractItemView):
    """
    View that is responsible for displaying Hints in a tab-based manner.
    """
    def __init__(self, parent=None):
        super(ResultsTabView, self).__init__(parent)

        self._canvas_manager = XicamCanvasManager()
        self._tabWidget = QTabWidget()
        self._tabWidget.setParent(self)
        # self._canvas_types = canvasmanager.canvas_types

        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().addWidget(self._tabWidget)

        self._plotdataitems = []

    def selectionChanged(self, selected: QItemSelection, deselected: QItemSelection) -> None:
        # TODO: try to use a shared selection model between the views (dataselectorview, resultsviews)
        # currently the dataChanged slot is used, which checks if the checkstate has changed
        print("selection changed.")

    def _findTabByName(self, tabName: str):
        """
        Convenience function to find a tab by name (instead of by index as provide by Qt's API).

        Parameters
        ----------
        tabName
            Name of the tab to attempt to find.

        Returns
        -------
        QWidget
            If found, returns the found widget with name ``tabName``.
            Raises an IndexError if not found.

        """
        for i in range(self._tabWidget.count()):
            if self._tabWidget.tabText(i) == tabName:
                return self._tabWidget.widget(i)
        raise IndexError

    def _findTabByCanvas(self, canvas: IntentCanvas):
        for i in range(self._tabWidget.count()):
            if self._tabWidget.widget(i) is canvas:
                return self._tabWidget.widget(i)

    def render(self, intent, canvas):
        # TODO : we don't need to do this find by canvas... we have it already
        found_canvas = None
        try:
            found_canvas = self._findTabByCanvas(canvas)
        except IndexError:
            pass
        if found_canvas:
            found_canvas.render(intent)
        else:
            # TODO rely on canvas manager to get the name of the canvas
            self._tabWidget.addTab(canvas, type(canvas).__name__)
            canvas.render(intent)

    def unrender(self, intent, canvas):
        # TODO: how do we feed the return val back to the canvas manager?
        canvas_removable = canvas.unrender(intent)
        return canvas_removable

    def dataChanged(self, topLeft: QModelIndex, bottomRight: QModelIndex, roles=None):
        """
        Re-implements the QAbstractItemView.dataChanged() slot
        """
        print("ResultsViewThing.dataChanged")
        check_state = bottomRight.data(Qt.CheckStateRole)
        canvas = self.model().data(bottomRight, EnsembleModel.canvas_role)
        # canvas_ = bottomRight.data(EnsembleModel.canvas_role)
        # intent = self.model().data(bottomRight, EnsembleModel.object_role)
        intent = bottomRight.data(EnsembleModel.object_role)

        if check_state == Qt.Unchecked:
            self.unrender(intent, canvas)

        else:
            self.render(intent, canvas)

    def horizontalOffset(self):
        return 0

    def indexAt(self, point: QPoint):
        return QModelIndex()

    def moveCursor(
        self,
        QAbstractItemView_CursorAction,
        Union,
        Qt_KeyboardModifiers=None,
        Qt_KeyboardModifier=None,
    ):
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
    ...



def main():
    app = QApplication(sys.argv)
    ex = StackedResultsWidget()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
