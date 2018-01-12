from qtpy.QtWidgets import *
from qtpy.QtGui import *
from xicam.gui.static import path
from pyqtgraph.parametertree import ParameterTree, Parameter
from pyFAI import detectors


class MaskingPanel(QWidget):
    def __init__(self):
        super(MaskingPanel, self).__init__()
        vbox = QVBoxLayout()

        # Setup UI
        self.maskproperties = ParameterTree()
        self.masklistview = MaskView()
        self.masktoolbar = QToolBar()
        self.addmaskbutton = QToolButton()
        self.addmaskmenu = QMenu()
        self.addpolygonaction = QAction('Polygon Mask')
        self.addpolygonaction.triggered.connect(self.addpolygonmask)
        self.adddetectoraction = QAction('Detector Mask')
        self.adddetectoraction.triggered.connect(self.adddetectormask)
        self.addzingeraction = QAction('Zinger Mask')
        self.addzingeraction.triggered.connect(self.addzingermask)
        self.addthresholdaction = QAction('Threshold Mask')
        self.addthresholdaction.triggered.connect(self.addthresholdmask)
        self.addmaskmenu.addActions(
            [self.addpolygonaction, self.adddetectoraction, self.addzingeraction, self.addthresholdaction])
        self.addmaskbutton.setText('Add mask')
        self.addmaskbutton.setIcon(QIcon(str(path('icons/plus.png'))))
        self.addmaskbutton.setMenu(self.addmaskmenu)
        self.addmaskbutton.setPopupMode(QToolButton.InstantPopup)
        self.masktoolbar.addWidget(self.addmaskbutton)
        self.masktoolbar.addAction(QIcon(str(path('icons/minus.png'))),
                                   'Remove mask',
                                   self.removemask)
        # self.masktoolbar.addAction(QIcon(str(path('icons/up.png'))),
        #                            'Move mask up',
        #                            self.moveup)
        # self.masktoolbar.addAction(QIcon(str(path('icons/down.png'))),
        #                            'Move mask down',
        #                            self.movedown)
        self.masktoolbar.addAction(QIcon(str(path('icons/save.png'))),
                                   'Save masks',
                                   self.savemasks)
        self.masktoolbar.addAction(QIcon(str(path('icons/open.png'))),
                                   'Save masks',
                                   self.openmasks)

        vbox.addWidget(self.maskproperties)
        vbox.addWidget(self.masklistview)
        vbox.addWidget(self.masktoolbar)

        # Setup model
        self.maskmodel = QStandardItemModel()
        self.masklistview.setModel(self.maskmodel)

        self.setLayout(vbox)

    def addpolygonmask(self):
        self.maskmodel.appendRow(PolygonMask())
        self.selectlast()

    def adddetectormask(self):
        self.maskmodel.appendRow(DetectorMask())
        self.selectlast()

    def addzingermask(self):
        self.maskmodel.appendRow(ZingerMask())
        self.selectlast()

    def addthresholdmask(self):
        self.maskmodel.appendRow(ThresholdMask())
        self.selectlast()

    def selectlast(self):
        self.masklistview.setCurrentIndex(self.maskmodel.item(self.maskmodel.rowCount() - 1).index())

    def removemask(self):
        indexes = self.masklistview.selectionModel().selectedRows()

        for index in reversed(indexes):
            self.maskmodel.removeRows(index.row(), 1)

    def savemasks(self):
        pass

    def openmasks(self):
        pass

    def movedown(self):
        pass

    def moveup(self):
        pass


class MaskView(QListView):
    def currentChanged(self, current, previous):
        if current.isValid():
            self.parent().maskproperties.setParameters(self.model().itemFromIndex(current).parameter, showTop=False)


class PolygonMask(QStandardItem):
    def __init__(self):
        super(PolygonMask, self).__init__('Polygon Mask')

        children = [{'name': 'Redraw polygon mask', 'type': 'action'}]
        self.parameter = Parameter(name='Polygon mask', type='group', children=children)


class DetectorMask(QStandardItem):
    def __init__(self):
        super(DetectorMask, self).__init__('Detector Mask')

        detectordict = {'Automatic': None}
        detectordict.update({d().name: d for d in detectors.ALL_DETECTORS.values()})
        children = [{'name': 'Detector', 'type': 'list', 'values': detectordict}]
        self.parameter = Parameter(name='Detector mask', type='group', children=children)


class ZingerMask(QStandardItem):
    def __init__(self):
        super(ZingerMask, self).__init__('Zinger Mask')

        children = [{'name': 'ZINGER MASK OPTIONS HERE', 'type': 'group'}]
        self.parameter = Parameter(name='Zinger mask', type='group', children=children)


class ThresholdMask(QStandardItem):
    def __init__(self):
        super(ThresholdMask, self).__init__('Threshold Mask')
        children = [{'name': 'Minimum', 'type': 'int', 'value': 0},
                    {'name': 'Maximum', 'type': 'int', 'value': 1e10}]
        self.parameter = Parameter(name='Threshold mask', type='group', children=children)
