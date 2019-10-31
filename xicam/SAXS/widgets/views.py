import numpy as np
import pyqtgraph as pg
from pyqtgraph.graphicsItems.LegendItem import ItemSample
from qtpy.QtCore import QItemSelection, QPersistentModelIndex, Qt
from qtpy.QtGui import QPen, QStandardItem, QStandardItemModel
from qtpy.QtWidgets import QAbstractItemView, QGridLayout, QLayout, QLineEdit, QListView, QSplitter, QToolBar, QTreeView, QVBoxLayout, QWidget

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


from xicam.gui.widgets.imageviewmixins import LogScaleIntensity
class TwoTimeImage(LogScaleIntensity):
    def __init__(self, *args, **kwargs):
        super(TwoTimeImage, self).__init__(self, *args, **kwargs)

    def setImage(self, img, autoRange=True, autoLevels=True, levels=None, axes=None, xvals=None, pos=None, scale=None, transform=None, autoHistogramRange=True):
        axes = {}
        super(TwoTimeImage, self).setImage(img)




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

    def __init__(self, collapseView, canvas, parent=None):
        super(DerivedDataWidget, self).__init__(parent)

        self.collapseView = collapseView
        self.canvas = canvas

        # self.collapseView.selectionChanged.connect(self.collapseView.)

        toolBar = QToolBar()
        action = toolBar.addAction(self.collapseView.name, self.collapseView.toggle)
        action.setIconText("&" + action.text())
        self.collapseView.toggled.connect(self.toggle)
        self.collapseButton = toolBar.widgetForAction(action)
        self.collapseButton.setCheckable(True)
        self.collapseButton.setChecked(not self.collapseView.collapsed)

        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.collapseView)
        self.splitter.addWidget(self.canvas)
        self.splitter.setCollapsible(0, self.collapseView.collapsed)
        self.splitter.setCollapsible(1, False)

        layout = QGridLayout()
        layout.addWidget(self.splitter, 0, 0)
        layout.addWidget(toolBar, 1, 0)

        self.setLayout(layout)

    def toggle(self, collapsed):
        self.collapseButton.setChecked(not collapsed)
        self.splitter.setCollapsible(0, collapsed)
        try:
            if collapsed:
                # print(self.splitter.sizes())
                # print(self.splitter.widget(0).minimumSizeHint())
                sizes = []
                for i in range(self.splitter.count()):
                    sizes.append(self.splitter.widget(i).minimumSizeHint().width())
                sizes[0] = 0
                self.splitter.setSizes(sizes)
            else:
                sizes = []
                for i in range(self.splitter.count()):
                    sizes.append(self.splitter.sizes()[i])
                sizes[0] = self.splitter.widget(i).minimumSizeHint().width()
                self.splitter.setSizes(sizes)
        except Exception as e:
            import traceback
            traceback.print_exc()


class DerivedDataCanvas(QWidget):

    def __init__(self, model):
        super(DerivedDataCanvas, self).__init__()
        self.model = model

    def clear(self):
        raise NotImplementedError

    def legend(self):
        raise NotImplementedError

    def plot(self, x, y, **kwargs):
        raise NotImplementedError

    def setImage(self, value, **kwargs):
        raise NotImplementedError


class OneTimeCanvas(DerivedDataCanvas):

    def __init__(self, model):
        super(OneTimeCanvas, self).__init__(model)
        self.plotWidget = CurveLabels()
        plotItem = self.plotWidget.getPlotItem()
        plotItem.setLabel('left', 'g<sub>2</sub>(&tau;)', 's')
        plotItem.setLabel('bottom', '&tau;', 's')
        layout = QGridLayout()
        layout.addWidget(self.plotWidget)
        self.setLayout(layout)

    # The DerivedDataWidget should connect its selection changed to workflow.visualize

    def clear(self):
        self.plotWidget.clear()

    def plot(self, x, y, **kwargs):
        self.clear()

        # selectedIndexes = []
        # for item in
        #     selectedIndexes.append(index)

        self.plotWidget.plot(x, y, **kwargs)


class TwoTimeCanvas(DerivedDataCanvas):

    def __init__(self, model):
        super(TwoTimeImage, self).__init__(DerivedDataCanvas)

    def clear(self):
        ...

    def setImage(self, value, **kwargs):
        ...


from qtpy.QtWidgets import QTabWidget
from qtpy.QtCore import QModelIndex, QPersistentModelIndex


class CheckableStandardItemModel(QStandardItemModel):

    def __init__(self, parent=None):
        super(CheckableStandardItemModel, self).__init__(parent)

        self._checkItems = set()

    def flags(self, index: QModelIndex):
        defaultFlags = self.flags(index)
        if index.isValid():
            return defaultFlags | Qt.ItemIsUserCheckable
        return defaultFlags

    def setData(self, index: QModelIndex, value, role=None):
        pass


class HintTabView(QAbstractItemView):

    def __init__(self, parent):
        super(HintTabView, self).__init__(parent)

        self._tabWidget = QTabWidget(self)

    # def dataChanged(self, QModelIndex, QModelIndex_1, roles, p_int=None, *args, **kwargs):
    #     pass

    def dataChanged(self, topLeft: QModelIndex, bottomRight: QModelIndex, roles):
        if not Qt.DisplayRole in roles:
            return

        # item = topLeft.

    def rowsInserted(self, QModelIndex, p_int, p_int_1):
        pass

    def rowsAboutToBeRemoved(self, QModelIndex, p_int, p_int_1):
        pass

    def visualRect(self, QModelIndex):
        pass

    def scrollTo(self, QModelIndex, hint=None):
        pass




if __name__ == "__main__":
    from qtpy.QtWidgets import QApplication, QMainWindow
    app = QApplication([])

    window = QMainWindow()
    collapseWidget = CollapsibleWidget(QListView(), "name")
    canvas = OneTimeCanvas(QStandardItemModel())
    widget = DerivedDataWidget(collapseWidget, canvas)
    canvas.plot(x=[1,2,3], y=[2,4,6])
    window.setCentralWidget(widget)
    window.show()

    app.exec()