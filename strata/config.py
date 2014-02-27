# -*- coding: utf-8 -*-

"""
# TODO: raise exception on **kwarg usage in Provider?

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

process notes:

* precursor reconciliation: provider argument names with known Variable names

"requirements" are Variables that must be successfully provided during
Config instantiation. If requirements isn't explicitly provided, it's
assumed that all Variables must be provided for a Config object to
successfully instantiate.

Put another way, at the ConfigSpec level, all variables need to have
at least one Provider, but the existence of a Provider doesn't mean
that the Provider will actually produce a value suitable for a given
Variable. The "requirements" construct provides a mechanism for
allowing a Config to generate an exception if a Variable is
unprovided, and allow other Variables to pass unprovided.

* How to differentiate between variables that are required, variables
  that are optional (will be tried not an error if not provided), and
  pruned variables (ones that aren't required and aren't dependencies
  of any other variables).

# TODO: set Pruned state on ProcessState
# TODO: is it ok to keep a reference to pstate/providers?
"""

from itertools import chain
from collections import namedtuple

from .core import Layer, DEBUG, Provider
from .utils import inject
from .errors import (ConfigException,
                     NotProvidable,
                     DependencyCycle,
                     UnresolvedDependency)


class StrataLayer(Layer):
    _autoprovided = ['config']

    def __init__(self, config):
        self._config = config

    def config(self):
        return self._config


class Resolution(object):
    def __init__(self, by, value=None):
        self.by = by
        self.value = value

    def __repr__(self):
        cn = self.__class__.__name__
        return '%s(by=%r, value=%r)' % (cn, self.by, self.value)


class Pruned(Resolution):
    def __init__(self, by=None, value=None):
        return super(Pruned, self).__init__(by, value)


class Satisfied(Resolution):
    pass


class Unsatisfied(Resolution):
    pass


# Gonna need a separate env-aware ConfigSpec thing, so as not to make
# the following too complex. That one will prolly have:
#     @property
#     def env_layer_map(self):
#        return dict([(ls.env, ls.layers) for ls in self.layersets])


class ConfigSpec(object):
    def __init__(self, variables, layerset):
        self.layerset = layerset
        self.variables = list(variables or [])
        self._compute()

    @classmethod
    def from_modules(cls, modules):
        """find all variables/layersets in the modules.
        One ConfigSpec per layerset.

        TODO: except/warn on overwrites/unused types?
        """
        return cls([], [])

    def make_config(self, name=None, reqs=None, default_defer=False):
        name = name or 'Config'
        reqs = set(self.variables) if reqs is None else set(reqs)

        # check requirements
        req_names = set([r.name for r in reqs])
        var_names = set([v.name for v in self.variables])
        if not req_names <= var_names:
            self._compute(reqs)  # TODO: check that recomputation is safe

        attrs = {'_config_spec': self,
                 '_requirements': reqs,
                 '_default_defer': default_defer}
        return type(name, (BaseConfig,), attrs)

    def _compute(self, requirements=None):
        # is requirements necessary here?
        requirements = requirements or []
        vpm = self.var_provider_map = {}
        vcm = self.var_consumer_map = {}
        layers = [StrataLayer] + self.layerset.layers

        reqs = list(self.variables)
        reqs.extend([r for r in requirements if r not in self.variables])
        autoprovided = [layer._get_autoprovided() for layer in layers]
        reqs.extend(chain.from_iterable(autoprovided))
        if DEBUG:
            print 'reqs:', sorted(set([r.name for r in reqs]))
        var_name_map = dict([(v.name, v) for v in reqs])
        to_proc = [v.name for v in reqs]
        unresolved = []
        while to_proc:
            cur_var_name = to_proc.pop()
            var = var_name_map[cur_var_name]
            for layer in layers:
                try:
                    provider = layer._get_provider(var)
                except NotProvidable:
                    continue
                vpm.setdefault(var.name, []).append(provider)
                for dn in provider.dep_names:
                    vcm.setdefault(dn, []).append(provider)
                    if dn not in var_name_map:
                        unresolved.append(dn)
                        var_name_map[dn] = None
                        #to_proc.append(dn)
            if cur_var_name not in vpm:
                raise UnresolvedDependency('no providers found for: %r' % var)
        if unresolved:
            raise UnresolvedDependency('unresolved deps: %r' % unresolved)
        self.all_providers = sum(vpm.values(), [])
        self.all_var_names = sorted(vpm.keys())

        sdm = self.slot_dep_map = self._compute_slot_dep_map(vpm)
        srdm = self.slot_rdep_map = self._compute_rdep_map(sdm)
        sorted_dep_slots = jit_toposort(srdm)
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
    def _compute_slot_dep_map(var_provider_map, preprovided=None):
        preprovided = preprovided or set()
        slot_dep_map = {}  # args across all layers
        for var, providers in var_provider_map.items():
            if var in preprovided:
                slot_dep_map[var] = set()
            else:
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
                    raise DependencyCycle('circular deps, I think: %r' % var)
                cur = to_proc.pop()
                cur_rdeps = dep_map.get(cur, [])
                to_proc.extend([c for c in cur_rdeps if c not in to_proc])
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


def _get_consumer_depth(name, vcm):
    to_proc = list(vcm.get(name, []))
    if not to_proc:
        return 1
    return max([_get_consumer_depth(cn, vcm) for cn in to_proc]) + 1


class ConfigProcessor(object):
    def __init__(self, config, debug=DEBUG):
        self.config = config
        self.requirements = self.config._requirements
        self.req_names = set([v.name for v in self.requirements])

        self.name_value_map = {}
        self.name_satisfier_map = {}
        self.name_result_map = {}  # only stores most recent result
        self.provider_result_map = {}
        self._debug = debug

        self._init_layers()
        self._init_providers()

    def _init_layers(self):
        self._strata_layer = StrataLayer(self.config)
        layer_type_pairs = [(StrataLayer, self._strata_layer)]
        layer_type_pairs.extend([(t, t()) for t in
                                 self.config._config_spec.layerset.layers])
        self.layers = [ltp[1] for ltp in layer_type_pairs]
        self.layer_map = dict(layer_type_pairs)

    def _init_providers(self):
        vpm = self.config._config_spec.var_provider_map
        bpm = self.bound_provider_map = {}
        for name, provider_list in vpm.items():
            bound_providers = [cp.get_bound(self.layer_map[cp.layer_type])
                               for cp in provider_list]
            bpm[name] = bound_providers
        # TODO: cleaner way to make config_provider ?
        config_provider = Provider(self._strata_layer, 'config', lambda: self)
        self.satisfy(config_provider, self.config)

    def process(self):
        bpm = self.bound_provider_map
        # TODO: some sorting of requirements
        to_proc = sum([list(reversed(bpm[var_name]))
                       for var_name in self.req_names], [])
        while to_proc:
            cp = to_proc.pop()
            if cp in self.provider_result_map:
                continue  # already run/memoized
            if cp.var_name in self.name_value_map:
                continue  # already satisfied
            unsat_deps = [dep for dep in cp.dep_names
                          if dep not in self.name_value_map]
            # name_result_map instead of name_value_map? shouldn't matter.
            if unsat_deps:
                to_proc.append(cp)  # repush current
                for dep_name in unsat_deps:
                    if dep_name in self.name_value_map:
                        # TODO
                        print 'pre-tried but not satisfied, prolly failed'
                    to_proc.extend(list(reversed(bpm[dep_name])))
                continue
            try:
                value = inject(cp.func, self.name_value_map)
            except Exception as e:
                self.unsatisfy(cp, e)
            else:
                self.satisfy(cp, value)

    def is_satisfied(self, var_name):
        return var_name in self.name_value_map

    def satisfy(self, provider, value):
        # satisfy is the only one that actually updates the scope
        result = Satisfied(by=provider, value=value)
        self.name_value_map[provider.var_name] = value
        self.name_satisfier_map[provider.var_name] = provider
        return self.register_result(provider, result)

    def prune(self, provider, value):
        result = Pruned(by=provider, value=value)
        if self._debug:
            print ' == ', result
        return self.register_result(provider, result)

    def unsatisfy(self, provider, exception):
        result = Unsatisfied(by=provider, value=exception)
        if self._debug:
            print ' - ', result
        return self.register_result(provider, result)

    def register_result(self, provider, result):
        self.name_result_map[provider.var_name] = result
        self.provider_result_map[provider] = result
        return result

    def __repr__(self):
        return ('<%s: %s providers, %s variables, %s satisfied>'
                % (self.__class__.__name__,
                   len(self.provider_result_map),
                   len(self.name_result_map),
                   len(self.name_value_map)))


class BaseConfig(object):
    _config_spec = None
    _requirements = None
    _default_defer = False

    def __init__(self, **kwargs):
        cfg_spec = self._config_spec
        self._deferred = kwargs.pop('_defer', self._default_defer)

        self._input_kwargs = dict(kwargs)

        self._strata_layer = StrataLayer(self)
        layer_type_pairs = [(StrataLayer, self._strata_layer)]
        layer_type_pairs.extend([(t, t()) for t in cfg_spec.layerset.layers])
        self._layers = [ltp[1] for ltp in layer_type_pairs]
        self._layer_map = dict(layer_type_pairs)

        self._providers = [p.get_bound(self._layer_map[p.layer_type])
                           for p in cfg_spec.sorted_providers]
        self._provider_results = {}
        self._unresolved = set()

        self._result_map = {}

        if not self._deferred:
            self._process()

    def __repr__(self):
        # would a non-constructor style repr be more helpful?
        cn = self.__class__.__name__
        kw_str = ', '.join(['%s=%r' % (k, v) for k, v
                            in self._input_kwargs.items()])
        return '%s(%s)' % (cn, kw_str)

    def _pre_process(self):
        pass

    def _post_process(self):
        self.__dict__.update(self._result_map)

    def _process(self):
        req_names = set([v.name for v in self._requirements])

        self._pstate = self._config_proc = ConfigProcessor(self)

        self._config_proc.process()
        self._result_map = self._config_proc.name_value_map
        self._provider_results = self._config_proc.provider_result_map
        self._unresolved = req_names - set(self._result_map)

        if self._unresolved:
            sorted_unres = sorted(self._unresolved)
            raise ConfigException('could not resolve: %r' % sorted_unres)
        if DEBUG:
            print self._pstate
        self._post_process()
        return

    def _process_one(self, name, pstate):
        if pstate.is_satisfied(name):
            return pstate.name_value_map[name]
        # TODO what exception to raise
        cfg_spec = self._config_spec
        cur_providers = cfg_spec.var_provider_map[name]
        for cp in cur_providers:
            cur_reqs = cp.dep_names
            for cr in cur_reqs:
                self._process_one(cr, pstate)
            if not all([pstate.is_satisfied(cr) for cr in cur_reqs]):
                continue
            # TODO: cache bound version?
            cp_bound = cp.get_bound(self._layer_map[cp.layer_type])
            try:
                value = inject(cp_bound.func, pstate.name_value_map)
            except Exception as e:
                pstate.unsatisfy(cp, e)
            else:
                pstate.satisfy(cp, value)
                break
        return


# ProviderSortKey
PSK = namedtuple('PSK', 'slot_idx, layer_idx, agg_dep savings cons_c arg_c char_c')


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
    level_idx = level_idx_map[p.var_name]

    max_dep = max([level_idx_map[d] + 1 for d in p.dep_names] or [0])
    #slot_idx = max_dep - level_idx

    upstack_dep_lists = [up.dep_names for up in var_stack[:layer_idx]]
    upstack_dep_set = set(sum(upstack_dep_lists, ()))
    agg_dep = max_dep + len(upstack_dep_set) + layer_idx
    savings = len(savings_map.get(p, []))
    consumer_c = len(consumer_map.get(p.var_name, []))
    arg_c = len(p.dep_names)
    return PSK(level_idx, layer_idx, agg_dep, -savings, -consumer_c, arg_c, len(p.var_name))


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
        if not cur:
            break
        ret.append(cur)
        remaining = dict([(item, deps - cur) for item, deps
                          in remaining.items() if item not in cur])
    if remaining:
        raise ValueError('unresolvable dependencies: %r' % remaining)
    return ret


def jit_toposort(dep_map):
    "expects a dict of {item: set([deps])}"
    ret, orig_dep_map, dep_map = [], dep_map, dict(dep_map)
    if not dep_map:
        return []
    extras = set.union(*dep_map.values()) - set(dep_map)
    dep_map.update([(k, set()) for k in extras])
    remaining = dict(dep_map)
    ready = set()
    while remaining:
        cur = set([item for item, deps in remaining.items() if not deps])
        if not cur:
            break
        ready.update(cur)
        cur_used = set([r for r in ready
                        if any([r in orig_dep_map[c] for c in cur])])
        ret.append(cur_used)
        ready = ready - cur_used
        remaining = dict([(item, deps - cur) for item, deps
                          in remaining.items() if item not in cur])
    if ready:
        ret.append(ready)
    if remaining:
        raise ValueError('unresolvable dependencies: %r' % remaining)
    return ret[1:]  # nothing's every used before the first thing, so snip snip
