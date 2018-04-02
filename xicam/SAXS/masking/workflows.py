from xicam.core.execution.workflow import Workflow
from .detector import DetectorMaskPlugin


class MaskingWorkflow(Workflow):
    def __init__(self):
        super(MaskingWorkflow, self).__init__('Masking')

        detectormask = DetectorMaskPlugin()

        self.processes = [detectormask]
        self.autoConnectAll()
