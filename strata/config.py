# -*- coding: utf-8 -*-

"""

# TODO: raise exception on **kwarg usage in Provider
# TODO: gonna tons of negative test cases
# TODO: variable names can't start with underscore

words:

provider -> (layer, arg_names (aka deps))
consumer
dependency
arg[ument]
satisfy
unsatisfied
pruned
slot
stack
"""

from collections import namedtuple

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
    def __init__(self, by=None, value=None):
        return super(Pruned, self).__init__(by, value)


class Satisfied(Resolution):
    pass


class Unsatisfied(Resolution):
    pass


class LayerSet(object):  # TODO: do-want?
    pass


# Gonna need a separate env-aware ConfigSpec thing, so as not to make
# the following too complex. That one will prolly have:
#     def get_config_type(self):
#        # TODO: specify requirements here?
#        pass
#     @property
#     def env_layer_map(self):
#        return dict([(ls.env, ls.layers) for ls in self.layersets])


class ConfigSpec(object):
    def __init__(self, variables, layerset):  # TODO: defer option?
        self.layerset = layerset
        self.variables = list(variables or [])
        # default maps/indexes

        # var_provider_map
        # var_consumer_map
        # all_providers
        # all_var_names

        self._compute()

    @classmethod
    def from_modules(cls, modules):
        """find all variables/layersets in the modules.
        One ConfigSpec per layerset.

        TODO: except/warn on overwrites/unused types?
        """
        return cls()

    def make_config(self, name=None, reqs=None, default_defer=False):
        name = name or 'FancyConfig'  # TODO, clearly
        reqs = set(self.variables) if reqs is None else set(reqs)

        # check requirements
        req_names = set([r.name for r in reqs])
        var_names = set([v.name for v in self.variables])

        if not req_names <= var_names:
            self._compute(reqs)  # TODO: check that recomputation is safe

        attrs = {'config_spec': self,
                 'requirements': reqs,
                 'default_defer': default_defer}
        return type('Config', (Config,), attrs)

    def _compute(self, requirements=None):
        requirements = requirements or []
        # raise on insufficient providers
        vpm = self.var_provider_map = {}
        vcm = self.var_consumer_map = {}

        for layer in self.layerset:
            for var in self.variables + requirements:
                try:
                    provider = layer._get_provider(var)
                except ValueError:  # TODO: custom error
                    continue
                vpm.setdefault(var.name, []).append(provider)
                for dn in provider.dep_names:
                    vcm.setdefault(dn, []).append(provider)

        self.all_providers = sum(vpm.values(), [])
        self.all_var_names = sorted(vpm.keys())  # TODO: + pre-satisfied?

        sdm = self.slot_dep_map = self._compute_slot_dep_map(vpm)
        srdm = self.slot_rdep_map = self._compute_rdep_map(sdm)
        sorted_dep_slots = toposort(srdm)
        dep_indices, slot_order = {}, []
        for level_idx, level in enumerate(sorted_dep_slots):
            for var_name in level:
                dep_indices[var_name] = level_idx
                slot_order.append(var_name)
        self.slot_order = slot_order

        savings_map = self._compute_savings_map(vpm, srdm)

        pkm = self.provider_key_map = {}
        for p in self.all_providers:
            pkm[p] = p_sortkey(provider=p,
                               provider_map=vpm,
                               level_idx_map=dep_indices,
                               savings_map=savings_map,
                               consumer_map=vcm)

        sorted_provider_pairs = sorted(pkm.items(), key=lambda x: x[-1])
        self.sorted_providers = [p[0] for p in sorted_provider_pairs]

    @staticmethod
    def _compute_slot_dep_map(var_provider_map):
        slot_dep_map = {}  # args across all layers
        for var, providers in var_provider_map.items():
            slot_deps = sum([list(p.dep_names) for p in providers], [])
            slot_dep_map[var] = set(slot_deps)
        return slot_dep_map

    @staticmethod
    def _compute_rdep_map(dep_map):
        "compute recursive dependency map"
        rdep_map = {}
        for var, slot_deps in dep_map.items():
            to_proc, rdeps, i = [var], set(), 0
            while to_proc:
                i += 1  # TODO: better circdep handlin
                if i > 50:
                    raise Exception('circular deps, I think: %r' % var)
                cur = to_proc.pop()
                cur_rdeps = dep_map.get(cur, [])
                to_proc.extend(cur_rdeps)
                rdeps.update(cur_rdeps)
            rdep_map[var] = rdeps
        return rdep_map

    @staticmethod
    def _compute_savings_map(var_provider_map, slot_rdep_map):
        # aka cost of alternative implementations of a var
        provider_rdep_map = {}
        stack_provider_rdep_map = {}
        provider_savings = {}
        for var, providers in var_provider_map.items():
            for p in providers:
                deps = p.dep_names
                rdep_sets = [slot_rdep_map.get(d, set()) for d in deps]
                rdep_sets.append(set(deps))
                p_rdeps = set.union(*rdep_sets)
                provider_rdep_map[p] = p_rdeps
                provider_savings[p] = set()
                sprd_list = stack_provider_rdep_map.setdefault(var, [])
                if sprd_list:
                    for prev_p, prev_rdeps in sprd_list:
                        provider_savings[prev_p].update(p_rdeps)
                sprd_list.append((p, p_rdeps))
        return provider_savings


# This is now fixin to become an abstract base class, with or without
# capital letters.

class Config(object):
    config_spec = None
    requirements = None
    default_defer = False

    def __init__(self, env=None, **kwargs):
        # TODO: env detection/handling
        # TODO: sanity check config_spec? Or do that in a metaclass?
        self.deferred = kwargs.pop('_defer', self.default_defer)

        self._layers = [t() for t in self.config_spec.layerset]
        layer_obj_map = dict(zip(self.config_spec.layerset, self._layers))
        self._layer_map = layer_obj_map
        self.providers = [p.get_bound(layer_obj_map[p.layer_type])
                          for p in self.config_spec.sorted_providers]
        self._strata_layer = core.StrataLayer(self)

        self._resolved = {'config': Satisfied(self._strata_layer, self)}
        self._unresolved = set()  # buncha TODOs here

        self.results = {}

        if not self.deferred:
            self._process()

    def _process(self):
        # TODO: what to do about re-processin?
        # TODO: need to provide a way of specifying end-requirements
        cfg_spec = self.config_spec
        ref_tracker = dict([(k, set([p.var_name for p in ps]))
                            for k, ps in cfg_spec.var_consumer_map.items()])
        _cur_vals = {'config': self}
        provider_results = {}
        for provider in self.providers:
            var_name = provider.var_name
            if ref_tracker.get(var_name) is None:
                print 'pruning: ', provider, '(no refs)'
                provider_results[provider] = Pruned()
                continue
            elif var_name in _cur_vals:
                print 'pruning:', provider, '(already satisfied)'
                provider_results[provider] = Pruned()
                continue
            try:
                res = inject(provider.func, _cur_vals)
            except Exception as e:
                print 'exception:', repr(e)
                provider_results[provider] = Unsatisfied(by=provider, value=e)
            else:
                provider_results[provider] = Satisfied(by=provider, value=res)
                _cur_vals[var_name] = res
                for provider_dep_name in cfg_spec.slot_dep_map[var_name]:
                    ref_tracker[provider_dep_name].discard(var_name)

        self.results = _cur_vals
        self.provider_results = provider_results


# ProviderSortKey
PSK = namedtuple('PSK', 'agg_dep savings cons_c arg_c char_c')


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
    var_stack = provider_map[p.var_name]
    layer_idx = var_stack.index(p)
    upstack_dep_lists = [up.dep_names for up in var_stack[:layer_idx]]
    upstack_dep_set = set(sum(upstack_dep_lists, ()))
    max_dep = max([level_idx_map[d] for d in p.dep_names] or [0])
    agg_dep = max_dep + len(upstack_dep_set) + layer_idx
    savings = len(savings_map.get(p, []))
    consumer_c = len(consumer_map.get(p.var_name, []))
    arg_c = len(p.dep_names)
    return PSK(agg_dep, -savings, -consumer_c, arg_c, len(p.var_name))


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


def main():
    from core import ez_vars  # tmp
    layers = _ENV_LAYERS_MAP['dev']
    variables = ez_vars(layers)
    var_d = [v for v in variables if v.name == 'var_d'][0]
    cspec = ConfigSpec(variables, layers)
    conf_type = cspec.make_config(reqs=[var_d])
    conf = conf_type()
    return conf


if __name__ == '__main__':
    main()
