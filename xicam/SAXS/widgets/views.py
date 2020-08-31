from collections import OrderedDict

from qtpy.QtCore import QModelIndex, QPoint, Qt
from qtpy.QtGui import QKeyEvent
from qtpy.QtWidgets import (
    QAbstractItemView,
    QAction,
    QLabel,
    QMenu,
    QTabWidget,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from xicam.core import msg
from xicam.gui.widgets.collapsiblewidget import CollapsibleWidget

from xicam.XPCS.hints import Hint, PlotHintCanvas, ImageHintCanvas

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


class DerivedDataWidgetTestClass(QWidget):
    """
    Widget for viewing derived data.

    This widget contains two widgets: a collapsible one and a non-collapsible one.
    The collapsible widget can be collapsed/uncollapsed by clicking a tool button.
    The non-collapsible widget always remains visible in the widget.
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
        self._categories = {
            "raw": ImageHintCanvas,
            "avg": ImageHintCanvas,
            "g2": PlotHintCanvas,
            "2-time": ImageHintCanvas
        }
        for category, canvas_type in self._categories.items():
            self._tabWidget.addTab(canvas_type(), category)
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
            If found, returns the found widget with name ``tabName``.
            Raises an IndexError if not found.

        """
        for i in range(self._tabWidget.count()):
            if self._tabWidget.tabText(i) == tabName:
                return self._tabWidget.widget(i)
        raise IndexError

    def dataChanged(self, topLeft: QModelIndex, bottomRight: QModelIndex, roles=None):
        """
        Re-implements the QAbstractItemView.dataChanged() slot.

        When the data attached to the Qt.CheckStateRole has been changed,
        this will either render a Hint or remove the Hint visualization.

        Parameters
        ----------
        topLeft
            For now, the only index we are concerned with,
            which corresponds to the item's check state changing.
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
                if isinstance(hint, Hint):
                    if topLeft.data(Qt.CheckStateRole) == Qt.Checked:
                        if hint.category not in [
                            self._tabWidget.tabText(index)
                            for index in range(self._tabWidget.count())
                        ]:
                            canvas = hint.canvas(hint)()
                            self._tabWidget.addTab(canvas, hint.category)
                        else:
                            canvas = self._findTab(hint.category)
                        canvas.render(hint)
                    else:
                        hint.remove()
            super(ResultsTabView, self).dataChanged(topLeft, bottomRight, roles)

    # try to use a selection model here instead of dataChanged
    # take the diff of unselected, newselected: initialze canvases that are new, keep the old, dump the unselected

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




if __name__ == "__main__":
    from qtpy.QtWidgets import QApplication, QMainWindow
    from xicam.SAXS.data.ensemble import Ensemble, EnsembleModel

    class Catalog:
        def __init__(self, name):
            self.name = name

    app = QApplication([])

    model = EnsembleModel()
    catalog_names = [f"catalog {i}" for i in range(3)]
    catalogs = [Catalog(name) for name in catalog_names]
    ensemble = Ensemble()
    view = DataSelectorView()
    view.setModel(model)

    ensemble.append_catalogs(*catalogs)
    model.add_ensemble(ensemble)

    window = QMainWindow()
    window.setCentralWidget(view)
    window.show()
    app.exec_()
