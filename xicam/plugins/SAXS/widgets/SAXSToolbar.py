from qtpy.QtWidgets import *
from xicam.plugins.WidgetPlugin import QWidgetPlugin


class SAXSToolbar(QToolBar, QWidgetPlugin):
    name = 'SAXSToolbar'

    def __init__(self, tabwidget: QTabWidget):
        super(SAXSToolbar, self).__init__()

        self.tabwidget = tabwidget

        self.detectorcombobox = QComboBox()
        self.tabwidget.model.dataChanged.connect(self.updatedetectorcombobox)

        self.addWidget(self.detectorcombobox)

    def updatedetectorcombobox(self, start, end):
        if self.tabwidget.count():
            fields = self.tabwidget.currentWidget().header.fields()
            self.detectorcombobox.clear()
            self.detectorcombobox.addItems([fields])
