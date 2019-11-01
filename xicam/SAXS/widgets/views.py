from collections import OrderedDict

import numpy as np
import pyqtgraph as pg
from pyqtgraph.graphicsItems.LegendItem import ItemSample
from qtpy.QtCore import QModelIndex, QPoint, Qt
from qtpy.QtGui import QPen, QStandardItem, QStandardItemModel, QKeyEvent
from qtpy.QtWidgets import QAbstractItemView, QGridLayout, QLineEdit, QListView, QSplitter, QTabWidget, \
    QToolBar, QTreeView, QVBoxLayout, QWidget

from xicam.gui.widgets.collapsiblewidget import CollapsibleWidget
from xicam.gui.widgets.plotwidgetmixins import CurveLabels


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
    def __init__(self):
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
    def __init__(self):
        self.model = QStandardItemModel()
        super(TwoTimeWidget, self).__init__(self.model)
        plotItem = self._plot.getPlotItem()
        plotItem.setLabel('left', 't<sub>2</sub>', 's')
        plotItem.setLabel('bottom', 't<sub>1</sub>', 's')
        self.image = LogScaleIntensity()
        self.image.view = plotItem


        # # TODO -- remove this temp code for time time
        # if type(view) is TwoTimeWidget:
        #     import pyqtgraph as pg
        #     from xicam.gui.widgets.imageviewmixins import LogScaleIntensity
        #     # why multiple results?
        #     g2 = self._results[0]['g2'].value.squeeze()
        #     img = LogScaleIntensity()
        #     img.setImage(g2)
        #     img.show()
        #     ###


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

    def __init__(self, collapseView, staticView, parent=None):
        super(DerivedDataWidget, self).__init__(parent)

        self.collapseWidget = CollapsibleWidget(collapseView, "Results")
        self.staticView = staticView

        self.collapseWidget.addWidget(staticView)
        self.setLayout(self.collapseWidget.layout())


class HintTabView(QAbstractItemView):

    def __init__(self, parent=None):
        super(HintTabView, self).__init__(parent)

        self._tabWidget = QTabWidget()
        self._tabWidget.setParent(self)
        self._indexToTabMap = OrderedDict()

        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().addWidget(self._tabWidget)

    def _findTab(self, tabName):
        for i in range(self._tabWidget.count()):
            if self._tabWidget.tabText(i) == tabName:
                return self._tabWidget.widget(i)
        raise IndexError

    def dataChanged(self, topLeft: QModelIndex, bottomRight: QModelIndex, roles, p_int=None, *args, **kwargs):
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


class DerivedDataModelView(QTreeView):

    def __init__(self, parent=None):
        super(DerivedDataModelView, self).__init__(parent)

        self.setHeaderHidden(True)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionMode(QAbstractItemView.NoSelection)
        self.setExpandsOnDoubleClick(False)

        self.clicked.connect(self.resolveChecks)

    def keyPressEvent(self, event: QKeyEvent):
        event.accept()

    def resolveChecks(self, index: QModelIndex):
        if not self.model():
            return

        item = self.model().itemFromIndex(index)
        # The item has just been checked, need to see if there are children to check
        if item.data(Qt.CheckStateRole) == Qt.Unchecked:
            # TODO: Potential duplicate signal emissions (dataChanged on setCheckState())
            if item.isCheckable():
                item.setCheckState(Qt.Checked)
            if self.model().hasChildren(index):
                numChildren = self.model().rowCount(index)
                childrenIndexes = [self.model().index(row, 0, index) for row in range(numChildren)]
                for childIndex in childrenIndexes:
                    childItem = self.model().itemFromIndex(childIndex)
                    if childItem.isCheckable():
                        childItem.setCheckState(Qt.Checked)

            else: # index is a child
                parentIndex = index.parent()
                numChildren = self.model().rowCount(parentIndex)
                childrenIndexes = [self.model().index(row, 0, parentIndex) for row in range(numChildren)]
                if all([self.model().itemFromIndex(index).checkState() == Qt.Checked for index in childrenIndexes]):
                    self.model().itemFromIndex(parentIndex).setCheckState(Qt.Checked)
                else:
                    self.model().itemFromIndex(parentIndex).setCheckState(Qt.PartiallyChecked)

        else:
            if item.isCheckable():
                item.setCheckState(Qt.Unchecked)
            if self.model().hasChildren(index):
                if self.model().itemFromIndex(index).checkState() == Qt.PartiallyChecked:
                    raise NotImplementedError
                numChildren = self.model().rowCount(index)
                childrenIndexes = [self.model().index(row, 0, index) for row in range(numChildren)]
                for childIndex in childrenIndexes:
                    childItem = self.model().itemFromIndex(childIndex)
                    if childItem.isCheckable():
                        childItem.setCheckState(Qt.Unchecked)
            else:  # index is a child
                parentIndex = index.parent()
                numChildren = self.model().rowCount(parentIndex)
                childrenIndexes = [self.model().index(row, 0, parentIndex) for row in range(numChildren)]
                if any([self.model().itemFromIndex(index).checkState() == Qt.Checked for index in
                        childrenIndexes]):
                    self.model().itemFromIndex(parentIndex).setCheckState(Qt.PartiallyChecked)
                else:
                    self.model().itemFromIndex(parentIndex).setCheckState(Qt.Unchecked)


class MyModel(QStandardItemModel):
    def __init__(self):
        super(MyModel, self).__init__()

    def flags(self, index: QModelIndex):
        if not index.isValid():
            return None

        if index.column() == 0:
            flags = Qt.ItemIsEnabled
        else:
            flags = super(MyModel, self).flags(index)
        return flags


if __name__ == "__main__":
    from qtpy.QtWidgets import QApplication, QMainWindow, QAction
    app = QApplication([])

    window = QMainWindow()
    # collapseWidget = CollapsibleWidget(QListView(), "name")
    # canvas = OneTimeCanvas(QStandardItemModel())
    # widget = DerivedDataWidget(collapseWidget, canvas)
    # canvas.plot(x=[1,2,3], y=[2,4,6])

    layout = QVBoxLayout()

    model = MyModel()



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

    # proxyModel = MySortFilterProxyModel()
    # proxyModel.setSourceModel(model)

    lview = DerivedDataModelView()
    lview.setModel(model)
    # rview = QListView()
    rview = HintTabView()
    rview.setModel(model)
    # rview.setModel(proxyModel)

    widget = DerivedDataWidget(lview, rview)

    # view = HintTabView()
    # view.setModel(model)
    #
    # for i in range(3):
    #     item = QStandardItem(1)
    #     item.setData("text" + str(i), role=Qt.DisplayRole)
    #     model.appendRow(item)

    # widget = QTabBar()
    # widget.addTab("text")
    # widget.addTab("text 2")
    window.setCentralWidget(widget)
    window.show()

    app.exec()