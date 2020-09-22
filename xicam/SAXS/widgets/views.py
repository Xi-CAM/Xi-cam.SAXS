from qtpy.QtCore import QModelIndex, QPoint, Qt, QItemSelection
from qtpy.QtGui import QKeyEvent
from qtpy.QtWidgets import (
    QAbstractItemView,
    QAction,
    QMenu,
    QTabWidget,
    QTreeView,
    QVBoxLayout,
    QWidget, QListView,
)

from xicam.core import msg

from xicam.core.intents import Intent
from xicam.plugins.intentcanvasplugin import IntentCanvas
from xicam.gui.canvases import PlotIntentCanvas, ImageIntentCanvas

from xicam.XPCS.models import XicamCanvasManager, CanvasProxyModel, EnsembleModel


class ResultsWidget(QWidget):
    # TODO reorganize layout at the GUI plugin level
    # (this should not contain the DataSelectorView)
    def __init__(self, model, parent=None):
        super(ResultsWidget, self).__init__(parent)
        self._model = model
        # self._hintView = ResultsTabView()
        # self._canvasView = ResultsViewThing()
        # self._canvasView = QTreeView()

        # self._canvasView = ResultsViewThing()
        # self._proxy = CanvasProxyModel()
        # self._proxy.setSourceModel(self._model)
        # self._canvasView.setModel(self._proxy)

        # self._model.dataChanged.connect(self._canvasView.dataChanged)
        # self._model.dataChanged.connect(lambda _: print("ensemble (source) model dataChanged"))

        # self._selector = DataSelectorView()
        # TODO: use ResultsView (which has the tab and split view) here
        self._selector = QTreeView()
        self._selector.setModel(self._model)

        # self._model.dataChanged.connect(b)
        layout = QVBoxLayout()
        layout.addWidget(self._selector)
        self.setLayout(layout)



class ResultsViewThing(QAbstractItemView):
    def __init__(self, parent=None):
        super(ResultsViewThing, self).__init__(parent)

    # def setModel(self, model):
    #     super(ResultsViewThing, self).setModel(model)
    #     self.model().dataChanged.connect(self.dataChanged)

    def selectionChanged(self, selected, unselected):
        print("ResultsViewthing.selectionChanged")
        print(self.model())

    def dataChanged(self, topLeft, bottomRight, roles=None):
        print("ResultsViewThing.dataChanged")
        print(topLeft)
        print(topLeft.data(Qt.DisplayRole))
        data = self.model().data(bottomRight, EnsembleModel.canvas_role)
        # print(topLeft.data(self.model().sourceModel()))
        intent = bottomRight.data(EnsembleModel.object_role)
        canvas = bottomRight.data(EnsembleModel.canvas_role)
        canvas.render(intent)
        canvas.show()
        # intent =
        # canvas.render()

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


# A CanvasView
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
    # TODO -- this could probably be moved into a more generic class, e.g. CheckableTreeView
    """
    Tree view responsible for selecting which derived data to visualize.

    This view implements a checkable tree view, whereby the top-level nodes
    (ignoring the implicit root node)
    can be checked or unchecked to toggle the check state of all of their children nodes.
    Additionally, if only some of the children nodes are checked,
    the parent node will be partially checked.
    """

    def __init__(self, parent=None):
        super(DataSelectorView, self).__init__(parent)

        self.setHeaderHidden(True)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionMode(QAbstractItemView.NoSelection)
        self.setExpandsOnDoubleClick(False)
        self.contextMenu = QMenu()
        rename_action = QAction("Rename", self.contextMenu)
        self.addAction(rename_action)
        rename_action.triggered.connect(self._rename_triggered)
        delete_action = QAction("Delete", self.contextMenu)
        self.addAction(delete_action)
        delete_action.triggered.connect(self._delete_triggered)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._context_menu)

        # This was difficult to accomplish with a selection model (i.e. selectionChanged),
        # as it created circular signal emissions with dataChanged.
        # So, we use the clicked signal to toggle checkState.
        self.clicked.connect(self.resolveChecks)

    def _context_menu(self, point):
        index = self.indexAt(point)
        print(index)
        if index.isValid():
            print("valid")
            print(self.viewport().mapToGlobal(point))
            self.contextMenu.exec_(self.viewport().mapToGlobal(point))

    def _delete_triggered(self):
        msg.logMessage("DataSelectorView._delete_triggered not implemented")

    def _rename_triggered(self):
        msg.logMessage("DataSelectorView._rename_triggered not implemented")

    def keyPressEvent(self, event: QKeyEvent):
        # We want to ignore any key press events for now
        event.accept()

    def resolveChecks(self, index: QModelIndex):
        """
        Logic that controls how a clicked item and children items are checked and unchecked.

        When the clicked item is checked or unchecked
        (and when any children need to be checked or unchecked),
        this implicitly emits the itemChanged() signal
        (since the Qt.CheckStatRole data is changed).
        This is captured by the HintTabView to visualize and remove Hints as appropriate.

        Parameters
        ----------
        index
            The index of the item that was clicked.
        """

        if not self.model():
            return

        item = self.model().itemFromIndex(index)  # QStandardItem
        # The item has been clicked and its previous state is unchecked (we will check items)
        if item.data(Qt.CheckStateRole) == Qt.Unchecked:
            check = True
        # The item has been clicked and its previous state is checked (we will uncheck items)
        else:
            check = False
        # TODO: Potential duplicate signal emissions (dataChanged on setCheckState())
        # Will check / uncheck the item and its children recursively
        self._check_item(item, check)
        # Will check / uncheck the parent items and its parents recursively
        self._partial_check_item(item, check)

    def _check_item(self, item, check):
        """
        Check or uncheck the item and all of its children until reaching leaf items.

        Parameters
        ----------
        item
            The item to check or uncheck
        check : bool
            If True, checks the item. If False, unchecks the item.
        """
        if item.isCheckable():
            # Check or uncheck the item
            if check:
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)

            # Recursively check or uncheck children
            if self.model().hasChildren(item.index()):
                num_children = self.model().rowCount(item.index())
                children_indexes = [
                    self.model().index(row, 0, item.index()) for row in range(num_children)
                ]
                for child_index in children_indexes:
                    child_item = self.model().itemFromIndex(child_index)
                    self._check_item(child_item, check)

    def _partial_check_item(self, item, check):
        """
        Propagates check state changes upward in the tree recursively.

        Ensures that the tree is updated to reflect changes to check state of an item.
        For example, parent items will be marked as checked, partially checked, or unchecked,
        depending if all children are checked, any children are checked,
        or no children are checked.
        """
        # Check parent item and see how many of its children are checked
        model = self.model()
        parent_index = item.index().parent()
        if parent_index.isValid():
            num_child = self.model().rowCount(parent_index)
            child_indexes = [model.index(row, 0, parent_index) for row in range(num_child)]
            # The item was checked
            if check:
                # All children are checked; parent should be checked
                if all(
                    [
                        model.itemFromIndex(sibling_index).checkState() == Qt.Checked
                        for sibling_index in child_indexes
                    ]
                ):
                    model.itemFromIndex(parent_index).setCheckState(Qt.Checked)
                # Not all children checked (but at least one child, `item`);
                # parent partially checked
                else:
                    model.itemFromIndex(parent_index).setCheckState(Qt.PartiallyChecked)
            # The item was unchecked
            else:
                # At least one child is checked / partially checked;
                # parent must be partially checked
                if any(
                    [
                        model.itemFromIndex(child_index).checkState() == Qt.Checked
                        or model.itemFromIndex(child_index).checkState() == Qt.PartiallyChecked
                        for child_index in child_indexes
                    ]
                ):
                    model.itemFromIndex(parent_index).setCheckState(Qt.PartiallyChecked)
                # All children are unchecked; parent is unchecked
                else:
                    model.itemFromIndex(parent_index).setCheckState(Qt.Unchecked)

            # Recurse up tree via parent item
            self._partial_check_item(model.itemFromIndex(parent_index), check)

#
# class ResultsWidget(QWidget):
#
#     def __init__(self, *args, **kwargs):
#         super(ResultsWidget, self).__init__(*args, **kwargs)



