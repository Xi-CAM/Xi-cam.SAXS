from xicam.core.execution.workflow import Workflow
# from xicam.gui.widgets.ROI import LabelArrayProcessingPlugin
from xicam.plugins.operationplugin import OperationPlugin


# TODO -- move to more reusable area
class ROIWorkflow(Workflow):
    """
    Workflow for ROIs.

    Initializes with a LabelArray operation.

    The expected result output will be through the `label_array` variable (defined in LabelArrayProcessingPlugin).
    """
    def __init__(self):
        super(ROIWorkflow, self).__init__(name="ROIWorkflow")
        # self.add_operation(LabelArrayProcessingPlugin())
        # self.auto_connect_all()

    def prepend_operation(self, operation: OperationPlugin, auto_connect_all: bool = False):
        super(ROIWorkflow, self).insert_operation(0, operation)
        if auto_connect_all:
            self.auto_connect_all()

