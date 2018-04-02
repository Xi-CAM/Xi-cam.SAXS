from qtpy.QtWidgets import *
from qtpy.QtCore import *
from qtpy.QtGui import *
from xicam.plugins.WidgetPlugin import QWidgetPlugin
from xicam.gui.static import path


class SAXSToolbar(QToolBar, QWidgetPlugin):
    name = 'SAXSToolbar'

    def __init__(self, tabwidget: QTabWidget):
        super(SAXSToolbar, self).__init__()

        self.results = []

        self.tabwidget = tabwidget

        self.detectorcombobox = QComboBox()
        self.tabwidget.model.dataChanged.connect(self.updatedetectorcombobox)

        self.addWidget(self.detectorcombobox)
        self.addSeparator()
        self.modegroup = QActionGroup(self)
        self.rawaction = self.mkAction('icons/raw.png', 'Raw', checkable=True, group=self.modegroup, checked=True)
        self.addAction(self.rawaction)
        self.cakeaction = self.mkAction('icons/cake.png', 'Cake (q/chi plot)', checkable=True, group=self.modegroup)
        self.addAction(self.cakeaction)
        self.remeshaction = self.mkAction('icons/remesh.png', 'Remesh (GIWAXS)', checkable=True, group=self.modegroup)
        self.addAction(self.remeshaction)
        self.addSeparator()

    def updatedetectorcombobox(self, start, end):
        if self.tabwidget.count():
            devices = self.tabwidget.currentWidget().header.devices()
            self.detectorcombobox.clear()
            self.detectorcombobox.addItems(devices)

    def mkAction(self, iconpath: str = None, text=None, receiver=None, group=None, checkable=False, checked=False):
        actn = QAction(self)
        if iconpath: actn.setIcon(QIcon(QPixmap(str(path(iconpath)))))
        if text: actn.setText(text)
        if receiver: actn.triggered.connect(receiver)
        actn.setCheckable(checkable)
        if checked: actn.setChecked(checked)
        if group: actn.setActionGroup(group)
        return actn
