import sys

from qtpy.QtCore import QModelIndex, QPoint, Qt, QItemSelectionModel, \
                        QItemSelection
from qtpy.QtGui import QStandardItemModel, QIcon
from qtpy.QtWidgets import QApplication, QAbstractItemView, QTabWidget, QTreeView, QVBoxLayout, QHBoxLayout, \
                           QWidget, QStackedWidget,  QPushButton, QSplitter, QStyleFactory

from xicam.gui.static import path
from xicam.plugins.intentcanvasplugin import IntentCanvas
from xicam.XPCS.models import XicamCanvasManager, EnsembleModel


class CanvasView(QAbstractItemView):
    """
       View that is responsible for displaying Hints in a tab-based manner.
       """
    def __init__(self, parent=None):
        super(CanvasView, self).__init__(parent)
        self._canvas_manager = XicamCanvasManager()

    def selectionChanged(self, selected: QItemSelection, deselected: QItemSelection) -> None:
        # TODO: try to use a shared selection model between the views (dataselectorview, resultsviews)
        # currently the dataChanged slot is used, which checks if the checkstate has changed
        print("selection changed.")

    def render(self, intent, canvas):
        item = canvas.render(intent)

    def unrender(self, intent, canvas):
        # TODO: how do we feed the return val back to the canvas manager?
        canvas_removable = canvas.unrender(intent)
        # if canvas_removable:
        #     self.canvases.remove(canvas)
        #return canvas_removable

    def dataChanged(self, topLeft: QModelIndex, bottomRight: QModelIndex, roles=None):
        """
        Re-implements the QAbstractItemView.dataChanged() slot
        """
        print("ResultsViewThing.dataChanged")
        check_state = bottomRight.data(Qt.CheckStateRole)
        # canvas = self.model().data(bottomRight, EnsembleModel.canvas_role)
        canvas = self._canvas_manager.canvas_from_index(bottomRight)
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

    # def setModel(self, model): # real signature unknown; restored from __doc__
    #     super(CanvasView, self).setModel(model)

    def scrollTo(self, QModelIndex, hint=None):
        return

    def verticalOffset(self):
        return 0

    def visualRect(self, QModelIndex):
        from qtpy.QtCore import QRect

        return QRect()
    # Contains the tab view and split view

    def show_canvases(self):
        ...


# TODO: this should be a parent class (CanvasView) that ResultsTabView and ResultsSplitView inherit from
class ResultsTabView(CanvasView):
    """
    View that is responsible for displaying Hints in a tab-based manner.
    """

    def __init__(self, parent=None):
        super(ResultsTabView, self).__init__(parent)

        self._tabWidget = QTabWidget()
        self._tabWidget.setParent(self)

        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().addWidget(self._tabWidget)

    # def _findTabByName(self, tabName: str):
    #     """
    #     Convenience function to find a tab by name (instead of by index as provide by Qt's API).
    #
    #     Parameters
    #     ----------
    #     tabName
    #         Name of the tab to attempt to find.
    #
    #     Returns
    #     -------
    #     QWidget
    #         If found, returns the found widget with name ``tabName``.
    #         Raises an IndexError if not found.
    #
    #     """
    #     for i in range(self._tabWidget.count()):
    #         if self._tabWidget.tabText(i) == tabName:
    #             return self._tabWidget.widget(i)
    #     raise IndexError
    #
    # def _findTabByCanvas(self, canvas: IntentCanvas):
    #     for i in range(self._tabWidget.count()):
    #         if self._tabWidget.widget(i) is canvas:
    #             return self._tabWidget.widget(i)

    def show_canvases(self):
        self._tabWidget.clear()
        for row in range(self.model().rowCount()):
            canvas = self._canvas_manager.canvas_from_row(row, self.model())
            if canvas is not None:
                self._tabWidget.addWidget(canvas)

#TODO:
    # [ ] commit changes
    # [x] fix show canvases
    # [ ] check with nxs file
    # [ ] add setModel to stackedresultsWidget class

class StackedResultsWidget(QWidget):
    """
    Outer Widget for viewing results in different ways using the QStackedWidget with
    several pages one for tabview and others for different split views
    """

    def __init__(
        self, model
    ):
        super(StackedResultsWidget, self).__init__()
        self._model = model
        self._model.dataChanged.connect(self.display)

        # create object instances of the different layout/view widgets to be used on the different pages of the stacked widget
        #self.tab_view = TabView(catalogmodel, selectionmodel, widgetcls, stream, field)
        self.tab_view = ResultsTabView()
        self.tab_view.setModel(self._model)
        self.hor_view = SplitHorizontal()
        self.hor_view.setModel(self._model)
        self.vert_view = SplitVertical()
        self.vert_view.setModel(self._model)
        self.three_view = SplitThreeView()
        self.three_view.setModel(self._model)
        self.grid_view = SplitGridView()
        self.grid_view.setModel(self._model)

        self._active_layout = self.tab_view

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

    # def setModel(self, QAbstractItemModel): # real signature unknown; restored from __doc__
    #     """ setModel(self, QAbstractItemModel) """
    #     pass

    def display(self, *args, **kwargs):
        self._active_layout.show_canvases()

    def display_tab(self):
        self._active_layout = self.tab_view
        self.stackedwidget.setCurrentIndex(0)
        self.display()

    def display_hor(self):
        self._active_layout = self.hor_view
        self.stackedwidget.setCurrentIndex(1)
        self.display()

    def display_vert(self):
        self._active_layout = self.vert_view
        self.stackedwidget.setCurrentIndex(2)
        self.display()

    def display_three(self):
        self._active_layout = self.three_view
        self.stackedwidget.setCurrentIndex(3)
        self.display()

    def display_grid(self):
        self._active_layout = self.grid_view
        self.stackedwidget.setCurrentIndex(4)
        self.display()

class SplitView(CanvasView):
    """
    Displaying results in a (dynamic) split view.
    """

    def __init__(
        self,
        parent: QWidget = None
    ):
        super(SplitView, self).__init__(parent)
        self.layout = QHBoxLayout()

        self.max_canvases = 0

# TODO [ ] add note/hint if to few/many dataset selected
#      [ ] label dataset in view

class SplitHorizontal(SplitView):
    """ Displays data in wide view, 2 on top of each other with a horizontal, movable divider bar"""
    def __init__(self, *args, **kwargs):
        super(SplitHorizontal, self).__init__(*args, **kwargs)

        self.splitter = QSplitter(Qt.Vertical)
        self.splitter.setSizes([100, 200])
        self.splitter.addWidget(QWidget())
        self.splitter.addWidget(QWidget())

        self.layout.addWidget(self.splitter)
        self.setLayout(self.layout)
        QApplication.setStyle(QStyleFactory.create('Cleanlooks'))
        self.setGeometry(300, 300, 300, 200)

        self.max_canvases = 2

    def show_canvases(self):
        for i in range(self.max_canvases):
            canvas = self._canvas_manager.canvas_from_row(i, self.model())
            if canvas is not None:
                self.splitter.replaceWidget(i, canvas)


class SplitVertical(SplitView):
    """ Displays data in vertical view, 2 next to each other with a vertical, movable divider bar"""
    def __init__(self, *args, **kwargs):
        super(SplitVertical, self).__init__(*args, **kwargs)

        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setSizes([100, 200])

        self.layout.addWidget(self.splitter)
        self.setLayout(self.layout)
        QApplication.setStyle(QStyleFactory.create('Cleanlooks'))
        self.setGeometry(300, 300, 300, 200)

        self.max_canvases = 2

    def show_canvases(self):
        for i in range(self.max_canvases):
            canvas = self._canvas_manager.canvas_from_row(i, self.model())
            if canvas is not None:
                self.splitter.replaceWidget(i, canvas)


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

        self.max_canvases = 3

    def show_canvases(self):
        for i in range(self.max_canvases):
            canvas = self._canvas_manager.canvas_from_row(i, self.model())
            if canvas is not None:
                if i < 2:
                    self.top_splitter.replaceWidget(i, canvas)
                else:
                    self.outer_splitter.replaceWidget(1, canvas)


class SplitGridView(SplitView):
    def __init__(self, *args, **kwargs):
        super(SplitGridView, self).__init__(*args, **kwargs)

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

        self.max_canvases = 4

    def moveSplitter( self, index, pos):
        splt = self._spltA if self.sender() == self._spltB else self._spltB
        splt.blockSignals(True)
        splt.moveSplitter(index, pos)
        splt.blockSignals(False)

    def show_canvases(self):
        for i in range(self.max_canvases):
            canvas = self._canvas_manager.canvas_from_row(i, self.model())
            if canvas is not None:
                if i < 2:
                    self.top_splitter.replaceWidget(i, canvas)
                else:
                    self.bottom_splitter.replaceWidget(i-2, canvas)


class DataSelectorView(QTreeView):
    ...


def main():
    app = QApplication(sys.argv)
    ex = StackedResultsWidget()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
