from databroker.core import BlueskyRun

from xicam.core.data import ProjectionException
from xicam.SAXS.stages import CorrelationStage, CalibrateGUIPlugin


class SAXSPlugin(CalibrateGUIPlugin, CorrelationStage): #...):
    name = 'SAXS'

