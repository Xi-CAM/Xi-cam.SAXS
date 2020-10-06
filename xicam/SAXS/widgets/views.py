import sys

from qtpy.QtCore import QModelIndex, QPoint, Qt, QItemSelectionModel, \
    QItemSelection, QPersistentModelIndex
from qtpy.QtGui import QStandardItemModel, QIcon
from qtpy.QtWidgets import QApplication, QAbstractItemView, QTabWidget, QTreeView, QVBoxLayout, QHBoxLayout, \
                           QWidget, QStackedWidget,  QPushButton, QSplitter, QStyleFactory, QButtonGroup

from xicam.gui.static import path
from xicam.plugins.intentcanvasplugin import IntentCanvas
from xicam.XPCS.models import XicamCanvasManager, EnsembleModel


class CanvasView(QAbstractItemView):
    """Defines a Qt-view interface for rendering and unrendering canvases."""
    def __init__(self, parent=None):
        super(CanvasView, self).__init__(parent)
        self._canvas_manager = XicamCanvasManager()
        self.icon = QIcon()

    def render(self, intent, canvas):
        print(f"RENDERING {intent.name} to {canvas}")
        item = canvas.render(intent)

    def unrender(self, intent, canvas):
        # TODO: how do we feed the return val back to the canvas manager?
        print(f"UNRENDERING {intent.name} from {canvas}")
        canvas.unrender(intent)
        # if canvas_removable:
        #     self.canvases.remove(canvas)
        #return canvas_removable

    def dataChanged(self, topLeft: QModelIndex, bottomRight: QModelIndex, roles=None):
        """
        Re-implements the QAbstractItemView.dataChanged() slot
        """
        print(f"CanvasView.dataChanged({topLeft.data()}, {bottomRight.data()}, {roles}")
        if Qt.CheckStateRole in roles:
            check_state = bottomRight.data(Qt.CheckStateRole)
            # canvas = self.model().data(bottomRight, EnsembleModel.canvas_role)
            canvas = self._canvas_manager.canvas_from_index(bottomRight)
            # canvas_ = bottomRight.data(EnsembleModel.canvas_role)
            # intent = self.model().data(bottomRight, EnsembleModel.object_role)
            intent = bottomRight.data(EnsembleModel.object_role)

            if canvas:
                if check_state == Qt.Unchecked:
                    self.unrender(intent, canvas)

                else:
                    self.render(intent, canvas)

                self.show_canvases()

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

    def show_canvases(self):
        ...


class ResultsWidget(QWidget):
    def __init__(self, parent=None):
        super(ResultsWidget, self).__init__(parent)

    def clear_canvases(self):
        ...

    def show_canvases(self, canvases):
        ...


# TODO: this should be a parent class (CanvasView) that ResultsTabView and ResultsSplitView inherit from
class ResultsTabWidget(ResultsWidget):
    """
    View that is responsible for displaying Hints in a tab-based manner.
    """

    def __init__(self, parent=None):
        super(ResultsTabWidget, self).__init__(parent)

        self._tabWidget = QTabWidget()
        self._tabWidget.setParent(self)

        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().addWidget(self._tabWidget)

        self.icon = QIcon(path('icons/tabs.png'))

    def clear_canvases(self):
        self._tabWidget.clear()

    def show_canvases(self, canvases):
        self._tabWidget.clear()
        for canvas in canvases:
            if canvas is not None:
                self._tabWidget.addTab(canvas, "blah")  # TODO: change name of tab

#TODO:
    # [ ] commit changes
    # [x] fix show canvases
    # [ ] check with nxs file
    # [ ] add setModel to stackedresultsWidget class


class StackedResultsWidget(CanvasView):
    """
    Outer Widget for viewing results in different ways using the QStackedWidget with
    several pages one for tabview and others for different split views
    """

    def __init__(self, parent=None, model=None):
        super(StackedResultsWidget, self).__init__(parent)
        if model is not None:
            self.setModel(model)

        self.results_widgets = [
            ResultsTabWidget(),
            SplitHorizontal(),
            SplitVertical(),
            SplitThreeView(),
            SplitGridView()
        ]

        ### Create stacked widget and fill pages with different views (different layouts)
        self.stackedwidget = QStackedWidget(self)
        # Create a visual layout section for the buttons that are used to switch the views
        self.buttonpanel = QHBoxLayout()
        self.buttonpanel.addStretch(10)
        # Create a logical button grouping that will:
        #   - show the currently selected view (button will be checked/pressed)
        #   - allow for switching the buttons/views in a mutually exclusive manner (only one can be pressed at a time)
        self.buttongroup = QButtonGroup()

        def add_results_widgets():
            for i in range(len(self.results_widgets)):
                # Add the view to the stacked widget
                self.stackedwidget.addWidget(self.results_widgets[i])
                # Create a button, using the view's recommended display icon
                button = QPushButton(self)
                button.setCheckable(True)
                button.setIcon(self.results_widgets[i].icon)
                # Add the button to the logical button group
                self.buttongroup.addButton(button, i)
                # Add the button to the visual layout section
                self.buttonpanel.addWidget(button)

        add_results_widgets()

        def setup_default_widget():
            # The first button added to the buttongroup will be the currently selected button (and therefore view)
            self.buttongroup.button(0).setChecked(True)

        setup_default_widget()

        # Whenever a button is switched, capture its id (corresponds to integer index in our case)
        self.buttongroup.idToggled.connect(self.switch_view)
        # Whenever the widget in the stack changes, display the current widget
        self.stackedwidget.currentChanged.connect(self.display)

        # define outer layout & add stacked widget and button panel
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.stackedwidget)
        self.layout.addLayout(self.buttonpanel)
        self.setLayout(self.layout)

    # Ask the canvas manager for canvases, put into widgets
    # clear, then repopulate the widgets

    def switch_view(self, id, toggled):
        # when toggled==True, the the button is the new button that was switched to.
        # when False, the button is the previous button
        view = self.results_widgets[id]
        if not toggled:
            print("CLEANUP code")

        self.stackedwidget.setCurrentIndex(id)

    def display(self, id):
        self.stackedwidget.widget(id).clear_canvases()
        self.stackedwidget.widget(id).show_canvases(self._canvas_manager.canvases(self.model()))

    def show_canvases(self):
        self.stackedwidget.currentWidget().clear_canvases()
        self.stackedwidget.currentWidget().show_canvases(self._canvas_manager.canvases(self.model()))


class SplitView(ResultsWidget):
    """
    Displaying results in a (dynamic) split view.
    """

    def __init__(
        self,
        parent: QWidget = None
    ):
        super(SplitView, self).__init__(parent)
        # self.outer_splitter = QSplitter()
        # self.inner_splitter = QSplitter()
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

        self.layout.addWidget(self.splitter)
        self.setLayout(self.layout)
        QApplication.setStyle(QStyleFactory.create('Cleanlooks'))
        self.setGeometry(300, 300, 300, 200)

        self.max_canvases = 2

        self.icon = QIcon(path('icons/1x1hor.png'))

    def clear_canvases(self):
        for i in range(self.splitter.count()):
            widget = self.splitter.widget(i)
            widget.setParent(None)

    def show_canvases(self, canvases):
        for i in range(len(canvases)):
            if i < self.max_canvases:
                canvas = canvases[i]
                if canvas is not None:
                    self.splitter.addWidget(canvas)


class SplitVertical(SplitHorizontal):
    """ Displays data in vertical view, 2 next to each other with a vertical, movable divider bar"""
    def __init__(self, *args, **kwargs):
        super(SplitVertical, self).__init__(*args, **kwargs)

        self.splitter.setOrientation(Qt.Horizontal)
        self.icon = QIcon(path('icons/1x1vert.png'))


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

        self.icon = QIcon(path('icons/2x1grid.png'))

    def show_canvases(self, canvases):
        for splitter in [self.top_splitter, self.outer_splitter]:
            for i in range(splitter.count()):
                widget = splitter.widget(i)
                if widget is not self.top_splitter:  # Don't prune the embedded splitter
                    widget.setParent(None)

        self.top_splitter.addWidget(canvases[0])
        self.top_splitter.addWidget(canvases[1])
        self.outer_splitter.addWidget(canvases[2])


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

        self.icon = QIcon(path('icons/2x2grid.png'))

    def moveSplitter( self, index, pos):
        splt = self._spltA if self.sender() == self._spltB else self._spltB
        splt.blockSignals(True)
        splt.moveSplitter(index, pos)
        splt.blockSignals(False)

    def show_canvases(self, canvases):
        for splitter in [self.top_splitter, self.bottom_splitter]:
            for i in range(splitter.count()):
                widget = splitter.widget(i)
                widget.setParent(None)

        for canvas in canvases[:2]:
            self.top_splitter.addWidget(canvas)
        for canvas in canvases[2:]:
            self.bottom_splitter.addWidget(canvas)


class DataSelectorView(QTreeView):
    ...


def main():
    app = QApplication(sys.argv)
    ex = StackedResultsWidget()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
