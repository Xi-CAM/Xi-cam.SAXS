#! /usr/bin/env python
# -*- coding: utf-8 -*- 

from yapsy.IPlugin import IPlugin
from xicam.plugins import QWidgetPlugin
from xicam.gui import threads
from qtpy.QtWidgets import QVBoxLayout, QComboBox, QPushButton
from collections import OrderedDict

from astropy.modeling import fitting
from .factory import XicamSASModel
from .loader import load_models
import numpy as np

from pyqtgraph.parametertree import ParameterTree


class SASModelsWidget(QWidgetPlugin):
    '''
        documentation:
    '''
    name = 'SASModel'

    fitters = OrderedDict({
        'LinearLSQFitter': fitting.LinearLSQFitter,
        'LevMarLSQFitter': fitting.LevMarLSQFitter,
        'SLSQPLSQFitter': fitting.SLSQPLSQFitter
    })

    def __init__(self, *args, **kwargs):
        self.models_tree = load_models()
        self.categories = self.models_tree.keys()
        super().__init__(self, *args, *kwargs)

        # verticle layout
        vlayout = QVBoxLayout()

        # add a dropdown list of fitting routines
        self.fitterbox = QComboBox()
        self.fitterox.addItems(list(self.fitters.keys()))
        vlayout.addWidget(self.fitterbox)

        # add a dropdown list of categories
        self.catbox = QComboBox()
        self.catbox.addItems(self.categories)
        vlayout.addWidget(self.catbox)

        # add list of models in category
        cat = self.catbox.currentText()
        self.modelsbox = QComboBox()
        self.modelsbox.addItems(list(self.models_tree[cat]))
        vlayout.addWidget(self.modelsbox)

        # add parameter tree
        modelname = self.modelsbox.currentText()
        parameters = self.models_tree[cat][modelname]['params']
        param_tree = ParameterTree(showTop=False)
        param_tree.addParameters(self.parameters)
        vlayout.addWidget(param_tree)
        self.fittable = XicamSASModel(modelname, parameters)

        # add fit-button 
        fit_button = QPushButton('Fit')
        fit_button.setToolTip('Fit model to the data')
        vlayout.addWidget(fit_button)
        fit_button.clicked.connect(self.run)

    def update_model(self):
        cat = self.catbox.currentText()
        modelname = self.modelsbox.currentText()
        parameters = self.models_tree[cat][modelname]['params']
        self.fittable = XicamSASModel(modelname, parameters)
        for p in parameters:
            if not p.name() in self.fittable.param_names:
                raise KeyError
            # set fixed if true
            self.fittable.fixed[p.name()] = p.child('Fixed').value()
            # set bounds if available
            if p.child('Bounded').value():
                bounds = (p.child('Bounded').child('Lower').value(),
                          p.child('Bounded').child('Upper').value())
                self.fittable.bounds[p.name()] = bounds
            else:
                self.fittable.bounds[p.name()] = (-np.inf, np.inf)

    def update(self, t):
        self.opt = t
        return t

    def run(self, q, I, callback_slot=None):
        if callback_slot is None: callback_slot = lambda t: None
        self.update_model()
        key = self.fitterbox.currentText()
        fitting_method = self.fitters[key]()
        thread = threads.QThreadFuture(fitting_method,
                                       self.fittable,
                                       q,
                                       I,
                                       callback_slot=lambda t: callback_slot(self.update(t)))
        thread.start()
        return thread
