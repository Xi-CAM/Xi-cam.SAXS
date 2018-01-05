import numpy as np
from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *

from xicam.core import msg
from xicam.core.data import load_header

from xicam.plugins import GUIPlugin, GUILayout, manager as pluginmanager

class SAXSPlugin(GUIPlugin):
    name = 'SAXS'
    sigLog = Signal(int, str, str, np.ndarray)

    def __init__(self):
        self.stages = {'Calibrate': GUILayout(pluginmanager.getPluginByName('SAXSViewerPlugin','WidgetPlugin').plugin_object()),
                       'Mask': GUILayout(QLabel('Mask')),
                       'Reduce': GUILayout(QLabel('Reduce')),
                       'Compare': GUILayout(QLabel('Compare'))
                       }
        super(SAXSPlugin, self).__init__()

        self.stages['Calibrate'].centerwidget.setDocument(load_header(['/home/rp/data/YL1031/YL1031__2m_00000.edf','/home/rp/data/YL1031/YL1031__2m_00001.edf','/home/rp/data/YL1031/YL1031__2m_00002.edf']))
