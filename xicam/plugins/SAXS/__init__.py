import numpy as np
from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *

from xicam.core import msg

from xicam.plugins import GUIPlugin, GUILayout



class SAXSPlugin(GUIPlugin):
    name = 'SAXS'
    sigLog = Signal(int, str, str, np.ndarray)

    def __init__(self):
        self.stages = {'Calibrate': GUILayout(QLabel('Calibrate')),
                       'Mask': GUILayout(QLabel('Mask')),
                       'Reduce': GUILayout(QLabel('Reduce')),
                       'Compare': GUILayout(QLabel('Compare'))
                       }
        super(SAXSPlugin, self).__init__()

