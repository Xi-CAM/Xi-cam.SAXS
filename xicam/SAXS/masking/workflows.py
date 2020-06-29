from xicam.core.execution.workflow import Workflow
from .detector import detector_mask_plugin


class MaskingWorkflow(Workflow):
    def __init__(self):
        super(MaskingWorkflow, self).__init__('Masking')

        detectormask = detector_mask_plugin()

        self.add_operation(detectormask)
        self.auto_connect_all()
