from databroker.core import BlueskyRun

from xicam.core.data import ProjectionException
from xicam.SAXS.stages import CorrelationStage, CalibrateGUIPlugin, ReduceGUIPlugin


class SAXSPlugin(CalibrateGUIPlugin, ReduceGUIPlugin, CorrelationStage):  # ...):
    name = 'SAXS'
