#! /usr/bin/env python
# -*- coding: utf-8 -*-

import yaml
from collections import OrderedDict
from pyqtgraph.parametertree import Parameter

cfg = 'config.yml'

# Fitting related
_fixed = {'name': 'Fixed', 'value': True, 'type': 'bool'}
_bounds = [{'name': 'Lower', 'value': '-\u221E'}, {'name': 'Upper', 'value': '\u221E'}]
_bounded = {'name': 'Bounded', 'value': False, 'type': 'bool',
            'children': _bounds, 'visible': False, 'enabled': False}


# resolve metaclass conflict
class XiMetaParam(type(yaml.YAMLObject), type(Parameter)):
    pass


class XiCamParameter(yaml.YAMLObject, Parameter, metaclass=XiMetaParam):
    yaml_tag = u'!YMLParameter'

    def __init__(self, name, description, value, units, **kwags):
        Parameter.__init__(self, name=name, value=value, \
                           title=description, children=[_fixed, _bounded])

    def __repr__(self):
        return "%s (%r, value=%r)" % \
               (self.__class__.__name__, self.name(), self.value())

    @classmethod
    def from_yaml(cls, loader, node):
        opts = loader.construct_mapping(node)
        return cls(**opts)


def load_models():
    with open(cfg) as fp:
        yml = yaml.load(fp)

    model_tree = OrderedDict()
    for key, val in yml.items():
        models = OrderedDict()
        for name, params in val.items():
            _params = [p['param'] for p in params]
            models[name] = {'params': _params}
        model_tree[key] = models
    return model_tree


if __name__ == '__main__':
    models = load_models()
    model = models['Cylinder Functions']['Barbell']['params']
    print(model)
