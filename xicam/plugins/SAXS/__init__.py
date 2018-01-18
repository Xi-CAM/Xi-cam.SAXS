import numpy as np
from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *

from xicam.core import msg
from xicam.core.data import load_header, NonDBHeader

from xicam.plugins import GUIPlugin, GUILayout, manager as pluginmanager
from .calibration import CalibrationPanel
from .masking import MaskingPanel
from .widgets.SAXSSpectra import SAXSSpectra
from xicam.gui.widgets.tabview import TabView


class SAXSPlugin(GUIPlugin):
    name = 'SAXS'
    sigLog = Signal(int, str, str, np.ndarray)

    def __init__(self):
        self.tabview = TabView()
        self.headermodel = QStandardItemModel()
        self.tabview.setModel(self.headermodel)
        self.tabview.setWidgetClass(pluginmanager.getPluginByName('SAXSViewerPlugin', 'WidgetPlugin').plugin_object)
        self.stages = {
            'Calibrate': GUILayout(self.tabview,
                                   # pluginmanager.getPluginByName('SAXSViewerPlugin', 'WidgetPlugin').plugin_object()
                                   right=pluginmanager.getPluginByName('CalibrationSettings',
                                                                       'SettingsPlugin').plugin_object.widget,
                                   rightbottom=CalibrationPanel(),
                                   top=pluginmanager.getPluginByName('SAXSToolbar', 'WidgetPlugin').plugin_object(
                                       self.tabview)),
            'Mask': GUILayout(QLabel('Mask'),
                              right=MaskingPanel()),
            'Reduce': GUILayout(QLabel('Reduce'), bottom=SAXSSpectra()),
            'Compare': GUILayout(QLabel('Compare'))
        }
        super(SAXSPlugin, self).__init__()

    def appendHeader(self, header: NonDBHeader, **kwargs):
        item = QStandardItem('???')
        item.header = header
        self.headermodel.appendRow(item)
        self.headermodel.dataChanged.emit(QModelIndex(), QModelIndex())
