from collections import OrderedDict

import pyqtgraph as pg
from pyqtgraph.graphicsItems.LegendItem import ItemSample
from qtpy.QtCore import QModelIndex, QPersistentModelIndex, QPoint, Qt
from qtpy.QtGui import QPen, QStandardItem, QStandardItemModel, QKeyEvent
from qtpy.QtWidgets import QAbstractItemView, QLineEdit, QListView, QTabWidget, QTreeView, QVBoxLayout, QWidget

from xicam.gui.widgets.collapsiblewidget import CollapsibleWidget


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
        self.model.itemChanged.connect(self.updatePlot)

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


class DerivedDataWidget(QWidget):
    
    def __init__(self, model, parent=None):
        super(DerivedDataWidget, self).__init__(parent)
        
        self._model = model
        self._derivedDataView = DerivedDataTreeView()
        self._derivedDataView.setModel(self._model)
        self._hintView = HintTabView()
        self._hintView.setModel(self._model)
        self._derivedDataWidget = CollapsibleWidget(self._derivedDataView, "Results")
        self._derivedDataWidget.addWidget(self._hintView)
        self.setLayout(self._derivedDataWidget.layout())


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


class HintTabView(QAbstractItemView):
    """
    View that is responsible for displaying Hints in a tab-based manner.
    """

    def __init__(self, parent=None):
        super(HintTabView, self).__init__(parent)

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

    def dataChanged(self, topLeft: QModelIndex, bottomRight: QModelIndex, roles):
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
        if self.model():
            if Qt.CheckStateRole in roles:
                hint = topLeft.data(Qt.UserRole)
                if hint:
                    if topLeft.data(Qt.CheckStateRole) == Qt.Checked:
                        if hint.name not in [self._tabWidget.tabText(index) for index in range(self._tabWidget.count())]:
                            canvas = hint.init_canvas()
                            self._tabWidget.addTab(canvas, hint.name)
                        else:
                            canvas = self._findTab(hint.name)
                        hint.visualize(canvas)
                    else:
                        hint.remove()

    def horizontalOffset(self):
        pass

    def indexAt(self, point: QPoint):
        pass

    def moveCursor(self, QAbstractItemView_CursorAction, Union, Qt_KeyboardModifiers=None, Qt_KeyboardModifier=None):
        return QModelIndex()

    def rowsInserted(self, index: QModelIndex, start, end):
        pass

    def rowsAboutToBeRemoved(self, index: QModelIndex, start, end):
        pass

    def scrollTo(self, QModelIndex, hint=None):
        pass

    def verticalOffset(self):
        pass

    def visualRect(self, QModelIndex):
        pass


class DerivedDataTreeView(QTreeView):
    # TODO -- this could probably be moved into a more generic class, e.g. CheckableTreeView
    """
    Tree view responsible for selecting which derived data to visualize.

    This view implements a checkable tree view, whereby the top-level nodes (ignoring the implicit root node) can be
    checked or unchecked to toggle the check state of all of their children nodes. Additionally, if only some of the
    children nodes are checked, the parent node will be partially checked.
    """

    def __init__(self, parent=None):
        super(DerivedDataTreeView, self).__init__(parent)

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


class DerivedDataModel(QStandardItemModel):
    """
    Derived data model that disables user interaction with the items.

    This is done so the DerivedDataView can listen for clicked signals and then control the checking logic.
    Using the Qt.ItemIsEnabled flag prevents the user from direcly checking / unchecking the item.
    """
    def __init__(self):
        super(DerivedDataModel, self).__init__()

    def flags(self, index: QModelIndex):
        if not index.isValid():
            return None
        if index.column() == 0:
            flags = Qt.ItemIsEnabled
        else:
            flags = super(DerivedDataModel, self).flags(index)
        return flags


if __name__ == "__main__":
    from qtpy.QtWidgets import QApplication, QMainWindow, QAction
    app = QApplication([])

    window = QMainWindow()
    layout = QVBoxLayout()
    model = DerivedDataModel()

    from xicam.plugins.hints import PlotHint, ImageHint
    parentItem = QStandardItem("blah")
    parentItem.setCheckable(True)
    import numpy as np
    for i in range(3):
        hint = PlotHint(np.arange(10), np.random.random((10,)), name="1-Time")
        item = QStandardItem(hint.name)
        item.setData(hint, Qt.UserRole)
        item.setCheckable(True)
        parentItem.appendRow(item)
    hint = ImageHint(np.random.random((100,100)), xlabel="x", ylabel="y", name="2-Time")
    item = QStandardItem(hint.name)
    item.setData(hint, Qt.UserRole)
    item.setCheckable(True)
    parentItem.appendRow(item)
    model.appendRow(parentItem)

    lview = DerivedDataTreeView()
    lview.setModel(model)
    rview = HintTabView()
    rview.setModel(model)

    widget = DerivedDataWidgetTestClass(lview, rview)

    window.setCentralWidget(widget)
    window.show()

    app.exec()