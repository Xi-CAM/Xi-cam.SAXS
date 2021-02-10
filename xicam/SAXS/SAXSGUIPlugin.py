from databroker.core import BlueskyRun

from xicam.core.data import ProjectionException
from xicam.SAXS.stages import CorrelationStage


class SAXSPlugin(CorrelationStage): #...):
    name = 'SAXS'

