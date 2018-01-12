import numpy as np
from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *

from xicam.core import msg
from xicam.core.data import load_header,NonDBHeader

from xicam.plugins import GUIPlugin, GUILayout, manager as pluginmanager
from .calibration import CalibrationPanel
from .masking import MaskingPanel

class SAXSPlugin(GUIPlugin):
    name = 'SAXS'
    sigLog = Signal(int, str, str, np.ndarray)

    def __init__(self):
        self.stages = {
            'Calibrate': GUILayout(pluginmanager.getPluginByName('SAXSViewerPlugin', 'WidgetPlugin').plugin_object(),
                                   right=pluginmanager.getPluginByName('CalibrationSettings',
                                                                       'SettingsPlugin').plugin_object.widget,
                                   rightbottom=CalibrationPanel()),
            'Mask': GUILayout(QLabel('Mask'),
                              right=MaskingPanel()),
                       'Reduce': GUILayout(QLabel('Reduce')),
                       'Compare': GUILayout(QLabel('Compare'))
        }
        super(SAXSPlugin, self).__init__()


    def appendHeader(self, doc:NonDBHeader, **kwargs):
        self.stages['Calibrate'].centerwidget.setHeader(doc)
