from xicam.plugins.operationplugin import operation
import numpy as np
from pyFAI.ext.reconstruct import reconstruct

inpaint = operation(reconstruct, name='Inpaint (pyFAI.ext.reconstruct)')
#TODO: add categories

