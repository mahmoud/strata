# -*- coding: utf-8 -*-

from core import _KNOWN_VARS

from utils import getargspec, get_arg_names, inject

# TODO: this has to improve
from tests.test_basic import FirstLayer, SecondLayer
_ENV_LAYERS_MAP = {'dev': [FirstLayer, SecondLayer]}


class DepResult(object):
    def __init__(self, by):
        self.by = by

    def __repr__(self):
        cn = self.__class__.__name__
        return '%s(by=%r)' % (cn, self.by)


class Pruned(DepResult):
    pass


class Satisfied(DepResult):
    pass


class Unsatisfied(DepResult):
    pass


class Config(object):
    def __init__(self, **kwargs):
        self.env = kwargs.pop('env', None)
        if self.env is None:
            self.env = detect_env()  # TODO: member function?
        self._layer_types = _ENV_LAYERS_MAP[self.env]  # TODO
        self._layers = [t() for t in self._layer_types]

        self.deps = {}
        self.results = {}
        self.known_vars = _KNOWN_VARS.keys()  # TODO: ?

        self._satisfied = {'config': self,
                           'kwargs': self}
        self._unsatisfied = {}
        self._pruned = {}
        self._var_provider_map = vpm = {}
        self._var_consumer_map = vcm = {}
        for layer in self._layers:
            for name in dir(layer):
                func = getattr(layer, name)
                if not callable(func) or '__' in name:
                    continue
                arg_names = get_arg_names(func)
                vpm.setdefault(name, []).append((layer, arg_names))
                for an in arg_names:
                    vcm.setdefault(an, []).append((layer, name))
        self._vcm_expanded = vcmx = {}
        """fulfill the item such that its provision would eliminate the most
        variables that would have to be used"""

        for var, consumers in vcm.items():
            to_proc = []
            for layer, name in consumers:
                subdeps = vcm.get(name, [])
                vcmx.setdefault(var, set()).update()
        import pdb;pdb.set_trace()
        self._process()

    def _process(self):
        pass


def detect_env():
    # TODO
    return 'dev'


def main():
    conf = Config()
    return conf


if __name__ == '__main__':
    main()
