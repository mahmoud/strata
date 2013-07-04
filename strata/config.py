# -*- coding: utf-8 -*-

"""
# TODO: raise exception on **kwarg usage in Provider
# TODO: gonna tons of negative test cases

words:

provider -> (layer, arg_names (aka deps))
consumer
dependency
arg[ument]
satisfy
unsatisfied
pruned

priority:

* preserve layer order (required)
* in dependency-satisfaction order (required)
* highly-dependent alternatives (providers in the same var stack)
* many consumers
* few arguments
* short name?
"""

from core import _KNOWN_VARS

from utils import getargspec, get_arg_names, inject

# TODO: this has to improve
from tests.test_basic import FirstLayer, SecondLayer, ThirdLayer
_ENV_LAYERS_MAP = {'dev': [FirstLayer, SecondLayer, ThirdLayer]}


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

        #all_vars = sum([l.layer_provides().keys() for l in self._layers], [])
        #all_vars = set(all_vars)
        #fut_all_vars = core._KNOWN_VARS.keys()

        for layer in self._layers:  # TODO: refactor
            layer_provides = layer.layer_provides()
            for var_name, provider in layer_provides.items():
                vpm.setdefault(var_name, []).append(provider)
                for dn in provider.dep_names:
                    vcm.setdefault(dn, []).append(provider)

        all_providers = sum(vpm.values(), [])
        all_var_names = vpm.keys()  # TODO: + pre-satisfied?
        """fulfill the item such that its provision would eliminate the most
        references to variables, i.e., the next item whose downstream
        alternatives have a large number of dependencies."""

        # expand out all deps
        stacked_dep_map = {}  # args across all layers
        for var, providers in vpm.items():
            stacked_deps = sum([list(p.dep_names) for p in providers], [])
            stacked_dep_map[var] = set(stacked_deps)

        stacked_rdep_map = {}  # a var's args, and their args, etc.
        for var, stacked_deps in stacked_dep_map.items():
            to_proc, rdeps, i = [var], set(), 0
            while to_proc:
                i += 1  # TODO: better circdep handlin
                if i > 50:
                    raise Exception('circular deps, I think: %r' % var)
                cur = to_proc.pop()
                cur_rdeps = stacked_dep_map.get(cur, [])
                to_proc.extend(cur_rdeps)
                rdeps.update(cur_rdeps)
            stacked_rdep_map[var] = rdeps

        sorted_deps = toposort(stacked_rdep_map)

        provider_rdep_map = {}
        stack_provider_rdep_map = {}
        provider_savings = {}
        for var, providers in vpm.items():
            for p in providers:
                deps = p.dep_names
                rdep_sets = [stacked_rdep_map.get(d, set()) for d in deps]
                rdep_sets.append(set(deps))
                p_rdeps = set.union(*rdep_sets)
                provider_rdep_map[p] = p_rdeps
                provider_savings[p] = set()
                sprd_list = stack_provider_rdep_map.setdefault(var, [])
                if sprd_list:
                    for prev_p, prev_rdeps in sprd_list:
                        provider_savings[prev_p].update(p_rdeps)
                sprd_list.append((p, p_rdeps))

        dep_indices, dep_order = {}, []
        for level_idx, level in enumerate(sorted_deps):
            sorted_level = sorted(level)
            for var_idx, var_name in enumerate(sorted_level):
                dep_indices[var_name] = level_idx
                dep_order.append(var_name)

        def p_sortkey(provider):
            # see note above
            p = provider
            max_dep = max([dep_indices[d] for d in p.dep_names] or [0])
            savings = len(provider_savings[p])
            consumer_c = len(vcm.get(p.var_name, []))
            arg_c = len(p.dep_names)
            return max_dep, -savings, arg_c, -consumer_c, len(p.var_name)

        provider_idx_map = dict([(p, p_sortkey(p)) for p in all_providers])
        rdo = sorted(provider_idx_map.items(), key=lambda x: x[-1])
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
