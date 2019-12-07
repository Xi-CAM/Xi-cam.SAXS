from xicam.core.execution.workflow import Workflow
from xicam.gui.widgets.ROI import LabelArrayProcessingPlugin
from xicam.plugins.processingplugin import ProcessingPlugin


# TODO -- move to more reusable area
class ROIWorkflow(Workflow):
    """
    Workflow for ROIs.

    Initializes with a LabelArray operation.

    The expected result output will be through the `label_array` variable (defined in LabelArrayProcessingPlugin).
    """
    def __init__(self):
        super(ROIWorkflow, self).__init__(name="ROIWorkflow")
        self.addProcess(LabelArrayProcessingPlugin())
        self.autoConnectAll()

    def prependProcess(self, process: ProcessingPlugin, autoconnectall: bool = False):
        super(ROIWorkflow, self).insertProcess(0, process, autoconnectall)

