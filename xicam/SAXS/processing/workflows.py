from xicam.core.execution.workflow import Workflow
from xicam.SAXS.processing.arrayrotate import ArrayRotate
from xicam.SAXS.processing.arraytranspose import ArrayTranspose
from .qintegrate import QIntegratePlugin
from .chiintegrate import ChiIntegratePlugin
from .xintegrate import XIntegratePlugin
from .zintegrate import ZIntegratePlugin
from .cakeintegrate import CakeIntegratePlugin


class ReduceWorkflow(Workflow):
    def __init__(self):
        super(ReduceWorkflow, self).__init__('Reduce')

        self.qintegrate = QIntegratePlugin()
        self.chiintegrate = ChiIntegratePlugin()
        self.xintegrate = XIntegratePlugin()
        self.zintegrate = ZIntegratePlugin()

        self.processes = [self.qintegrate, self.chiintegrate, self.xintegrate, self.zintegrate]
        self.autoConnectAll()


class DisplayWorkflow(Workflow):
    def __init__(self):
        super(DisplayWorkflow, self).__init__('Display')

        self.cake = CakeIntegratePlugin()
        self.processes = [self.cake]
        self.autoConnectAll()
