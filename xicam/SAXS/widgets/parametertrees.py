from typing import Callable

from pyqtgraph.parametertree import Parameter, ParameterTree
from pyqtgraph.parametertree.parameterTypes import ActionParameter, ListParameter

from ..workflows.xpcs import OneTimeAlgorithms, TwoTimeAlgorithms


class CorrelationParameterTree(ParameterTree):
    """Parameter tree that captures XPCS correlation adjustable parameters.

    Starting point to attempt to allow selecting an 'algorithm'
    and then repopulating the parameter tree accordingly.
    Any visible input parameters in the associated workflow will be adjustable here.
    The workflow can also be run here.
    """
    def __init__(self, parent=None, showHeader=True, processor: Callable[[], None] = None):
        """Create the parameter tree, optionally providing a workflow.

        When a workflow is provided,

        Parameters
        ----------
        parent
            See pyqtgraph.ParameterTree.__init__.
        showHeader
            See pyqtgraph.ParameterTree.__init__.
        processor
            If provided, creates a 'Run' button that is connected to the callable passed (default is None).
            For example, this callable could grab the necessary data to pass into a workflow, then execute it.
        """
        super(CorrelationParameterTree, self).__init__(parent, showHeader)
        self._paramName = 'Algorithm'
        self._name = 'Correlation Processor'
        self.processor = processor
        self.param = None
        self.workflow = None
        self._workflows = dict()

        # List of algorithms available
        # key   -> algorithm name (workflow.name)
        # value -> algorithm callable (workflow)
        self.listParameter = ListParameter(name=self._paramName,
                                           values={'':''},
                                           value='')

        self.param = Parameter(name=self._name)
        self.param.addChild(self.listParameter)
        self.setParameters(self.param, showTop=False)

        if self.processor:
            # Button added separately since update removes then adds all children in self.param
            self.processButton = ActionParameter(name="Run")
            self.processButton.sigActivated.connect(self.processor)
            self.addParameters(self.processButton)

    def update(self, *_):
        """Update the parameter tree according to which algorithm (workflow) is selected."""
        # for child in self.param.children():  # this doesn't seem to work...
        for child in self.param.childs[1:]:
            child.remove()

        # Based on current workflow (listParameter value), re-populate the tree.
        self.workflow = self._workflows.get(self.listParameter.value().name, self.listParameter.value()())
        self._workflows[self.workflow.name] = self.workflow
        for operation in self.workflow.operations:
            self.param.addChild(Parameter(name=operation.name, type='group', children=operation.as_parameter()))


class OneTimeParameterTree(CorrelationParameterTree):
    """Defines a parameter tree for 1-time correlation."""
    def __init__(self, parent=None, showHeader=True, processor: Callable[[], None] = None):
        super(OneTimeParameterTree, self).__init__(parent, showHeader, processor)
        self._name = '1-Time Processor'
        self.listParameter.setLimits(OneTimeAlgorithms.algorithms())
        self.listParameter.setValue(OneTimeAlgorithms.algorithms()[OneTimeAlgorithms.default()])

        self.update()
        self.listParameter.sigValueChanged.connect(self.update)


class TwoTimeParameterTree(CorrelationParameterTree):
    """Defines a parameter tree for 2-time correlation."""
    def __init__(self, parent=None, showHeader=True, processor: Callable[[], None] = None):
        super(TwoTimeParameterTree, self).__init__(parent, showHeader, processor)
        self._name = '2-Time Processor'
        self.listParameter.setLimits(TwoTimeAlgorithms.algorithms())
        self.listParameter.setValue(TwoTimeAlgorithms.algorithms()[TwoTimeAlgorithms.default()])

        self.update()
        self.listParameter.sigValueChanged.connect(self.update)