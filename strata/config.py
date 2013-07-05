# -*- coding: utf-8 -*-

"""# TODO: raise exception on **kwarg usage in Provider
# TODO: gonna tons of negative test cases

words:

provider -> (layer, arg_names (aka deps))
consumer
dependency
arg[ument]
satisfy
unsatisfied
pruned
"""

import core
from utils import inject

# TODO: this has to improve
from tests.test_basic import FirstLayer, SecondLayer, ThirdLayer
_ENV_LAYERS_MAP = {'dev': [FirstLayer, SecondLayer, ThirdLayer]}


class Resolution(object):
    def __init__(self, by, value=None):
        self.by = by
        self.value = value

    def __repr__(self):
        cn = self.__class__.__name__
        return '%s(by=%r)' % (cn, self.by)


class Pruned(Resolution):
    pass


class Satisfied(Resolution):
    pass


class Unsatisfied(Resolution):
    pass


class Config(object):
    def __init__(self, env=None, **kwargs):
        self.env = kwargs.pop('env', None)
        if self.env is None:
            self.env = detect_env()  # TODO: member function?
        self._layer_types = _ENV_LAYERS_MAP[self.env]  # TODO
        self._layers = [t() for t in self._layer_types]
        self._strata_layer = core.StrataLayer(self)

        self.deps = {}
        self.results = {}

        self._cur_vals = {'config': self}
        self._resolved = {'config': Satisfied(self._strata_layer, self)}
        self._unresolved = set()  # buncha TODOs here
        # TODO: resolved/unresolved with Resolution subtypes

        self._var_provider_map = vpm = {}
        self._var_consumer_map = vcm = {}

        for layer in self._layers:
            layer_provides = layer.layer_provides()
            for var_name, provider in layer_provides.items():
                vpm.setdefault(var_name, []).append(provider)
                for dn in provider.dep_names:
                    vcm.setdefault(dn, []).append(provider)

        self._all_providers = sum(vpm.values(), [])
        self._all_var_names = vpm.keys()  # TODO: + pre-satisfied?

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

        dep_indices, basic_dep_order = {}, []
        for level_idx, level in enumerate(sorted_deps):
            sorted_level = sorted(level)
            for var_name in sorted_level:
                dep_indices[var_name] = level_idx
                basic_dep_order.append(var_name)

        provider_key_map = {}
        for p in self._all_providers:
            provider_key_map[p] = p_sortkey(provider=p,
                                            provider_map=vpm,
                                            level_idx_map=dep_indices,
                                            savings_map=provider_savings,
                                            consumer_map=vcm)

        self.rdo = sorted(provider_key_map.items(), key=lambda x: x[-1])
        self._process()

    def _process(self):
        self._unresolved = set([x for x in self._all_var_names
                                if x not in self._resolved])
        remaining_consumers = dict(self._var_consumer_map)  # TODO
        for provider, scores in self.rdo:
            var_name = provider.var_name
            cur_val = self._resolved.get(var_name)
            if isinstance(cur_val, (Satisfied, Pruned)):
                print 'pruning:', provider
                self._unresolved.discard(var_name)
                continue
            try:
                res = inject(provider.func, self._cur_vals)
            except Exception as e:
                print e
                # self._resolved[var_name] = Unsatisfied(by=provider)
            else:
                self._unresolved.discard(var_name)
                self._resolved[var_name] = Satisfied(by=provider, value=res)
                self._cur_vals[var_name] = res
        import pdb;pdb.set_trace()


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


def p_sortkey(provider, provider_map, level_idx_map, savings_map=None,
              consumer_map=None):
    """
    priority:

    * preserve layer order (required)
    * in dependency-satisfaction order (required)
    * savings (i.e., highly-dependent alternatives)
    * many consumers
    * few arguments
    * short name?

    'savings' enables sorting fulfillment order such that a variable's
    provisioning would eliminate the most references to other variables
    (pruning), i.e., the next item whose downstream alternatives have a
    large number of dependencies.
    """
    p = provider
    savings_map = savings_map or {}
    consumer_map = consumer_map or {}
    max_dep = max([level_idx_map[d] for d in p.dep_names] or [0])
    savings = len(savings_map.get(p, []))
    consumer_c = len(consumer_map.get(p.var_name, []))
    arg_c = len(p.dep_names)
    return max_dep, -savings, arg_c, -consumer_c, len(p.var_name)


def detect_env():
    # TODO
    return 'dev'


def main():
    conf = Config()
    return conf


if __name__ == '__main__':
    main()
