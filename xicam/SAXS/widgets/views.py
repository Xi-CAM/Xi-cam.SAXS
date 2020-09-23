from qtpy.QtCore import QModelIndex, QPoint, Qt, QItemSelection
from qtpy.QtWidgets import (
    QAbstractItemView,
    QTabWidget,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from xicam.plugins.intentcanvasplugin import IntentCanvas
from xicam.XPCS.models import XicamCanvasManager, EnsembleModel


# TODO: remove this class
class ResultsWidget(QWidget):
    def __init__(self, *args, **kwargs):
        pass


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
