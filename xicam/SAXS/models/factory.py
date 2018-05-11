#! /usr/bin/env python

from sasmodels.core import load_model
from sasmodels.direct_model import call_kernel
from astropy.modeling import Parameter
from astropy.modeling import Fittable1DModel


def create_param(v):
    return Parameter(v.name(), default=v.value())


def XicamSASModel(name, params):
    """
    XicamModel wraps sasmdoels from sasview (https://github.com/SasView/sasmodles),
    in a fittable 1-D plugin for Xi-cam. This object can be passed to astropy for
    data fitting.
    
    Parameters: 
        name (str) : name of the sasmoels (http://www.sasview.org/sasmodels/index.html)
        params (dict): key : value pairs of fittable parameters
    Returns:
        func (XicamFittable) : function that takes q-values and returns intensity values

"""
    inputs = [p.name() for p in params]
    model_name = name.lower().replace(' ', '_')
    m = load_model(model_name)

    # evaluate callback
    def saxs_curve(q, *args):
        kernel = m.make_kernel([q])
        p_fit = dict(zip(inputs, args))
        return call_kernel(kernel, p_fit)

    # create an astropy fittable model
    names = {
        'name': 'SASFittable_' + name + 'Model',
        'inputs': inputs,
        'outputs': ['I'],
        'evaluate': staticmethod(saxs_curve)
    }
    p = dict((p.name(), create_param(p)) for p in params)
    names.update(p)
    return type('SASModelFittable', (Fittable1DModel,), names)()


def test():
    import matplotlib.pyplot as plt
    import numpy as np
    from pyqtgraph.parametertree import Parameter
    q = np.linspace(0, 1, 512)
    name = 'cylinder'
    r = Parameter.create(name='radius', value=200.)
    h = Parameter.create(name='height', value=1000.)
    params = [r, h]
    func = XicamSASModel(name, params)
    Iq = func(q)
    plt.loglog(q, Iq)
    plt.show()


if __name__ == '__main__':
    test()
