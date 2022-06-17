from databroker.core import BlueskyRun

from xicam.core.data import ProjectionException
from xicam.SAXS.stages import CorrelationStage, CalibrateGUIPlugin, ReduceGUIPlugin


class SAXSPlugin(CorrelationStage, ReduceGUIPlugin, CalibrateGUIPlugin):  # ...):
    name = 'SAXS'
