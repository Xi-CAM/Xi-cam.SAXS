from xicam.core.execution.workflow import Workflow
from .qintegrate import q_integrate
from .chiintegrate import chi_integrate
from .xintegrate import x_integrate
from .zintegrate import z_integrate
from .cakeintegrate import cake_integration


class ReduceWorkflow(Workflow):
    def __init__(self):
        super(ReduceWorkflow, self).__init__('Reduce')

        self.qintegrate = q_integrate()
        self.chiintegrate = chi_integrate()
        self.xintegrate = x_integrate()
        self.zintegrate = z_integrate()

        self.add_operations(self.qintegrate, self.chiintegrate, self.xintegrate, self.zintegrate)
        self.auto_connect_all()


class DisplayWorkflow(Workflow):
    def __init__(self):
        super(DisplayWorkflow, self).__init__('Display')

        self.cake = cake_integration()
        self.add_operation(self.cake)
        self.auto_connect_all()
