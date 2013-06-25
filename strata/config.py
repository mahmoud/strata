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
    def __init__(self, env=None, **kwargs):
        self.env = kwargs.pop('env', None)
        if self.env is None:
            self.env = detect_env()  # TODO: member function?
        self._layer_types = _ENV_LAYERS_MAP[self.env]  # TODO
        self._layers = [t() for t in self._layer_types]

        self.deps = {}
        self.results = {}

        self._satisfied = {'config': self,
                           'kwargs': self}
        self._unsatisfied = {}
        self._pruned = {}
        self._var_provider_map = vpm = {}
        self._var_consumer_map = vcm = {}

        all_vars = set(sum([l.layer_provides().keys() for l in self._layers], []))
        fut_all_vars = _KNOWN_VARS.keys()
        #for layer in self._layers:  # TODO: tmp way to build variable list
        #    for name in dir(layer):  # (it should come from VariableMeta)
        #        func = getattr(layer, name)
        #        if callable(func) and not name.startswith('__') \
        #           and name not in all_vars:
        #            all_vars.append(name)

        for var_name in all_vars:
            for layer in self._layers:  # TODO: refactor
                try:
                    func = layer.layer_provides()[var_name]
                except KeyError:
                    continue
                arg_names = get_arg_names(func)
                vpm.setdefault(var_name, []).append((layer, arg_names))
                for an in arg_names:
                    vcm.setdefault(an, []).append((layer, var_name))
        """fulfill the item such that its provision would eliminate the most
        variables that would have to be used"""

        # expand out all deps
        stacked_arg_map = {}  # args across all layers
        for var, layer_args in vpm.items():
            stacked_args = sum([list(args) for _, args in layer_args], [])
            stacked_arg_map[var] = set(stacked_args)

        recursive_arg_map = {}
        for var, stacked_args in stacked_arg_map.items():
            to_proc, rec_args, i = [var], set(), 0
            while to_proc:
                i += 1  # TODO: better circdep handlin
                if i > 50:
                    raise Exception('circular deps, I think: %r' % var)
                cur = to_proc.pop()
                cur_stargs = stacked_arg_map.get(cur, [])
                to_proc.extend(cur_stargs)
                rec_args.update(cur_stargs)
            recursive_arg_map[var] = rec_args

        sorted_deps = toposort(recursive_arg_map)
        import pdb;pdb.set_trace()
        self._process()

    def _process(self):
        pass


def toposort(dep_map):
    "expects a dict of {item: set([deps])}"
    ret, dep_map = [], dict(dep_map)
    if not dep_map:
        return []
    extras = set.union(*dep_map.values()) - set(dep_map)
    dep_map.update([(k, set()) for k in extras])
    remaining = dict(dep_map)
    while remaining:
        cur = set([item for item, deps in remaining.items() if not deps])
        if cur:
            ret.append(cur)
            remaining = dict([(item, deps - cur) for item, deps
                              in remaining.items() if item not in cur])
        else:
            break
    if remaining:
        raise ValueError('unresolvable dependencies: %r' % remaining)
    return ret


def detect_env():
    # TODO
    return 'dev'


def main():
    conf = Config()
    return conf


if __name__ == '__main__':
    main()
