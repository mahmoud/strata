# -*- coding: utf-8 -*-

from strata import Layer, ConfigSpec, Variable
from strata.core import ez_vars  # TODO
from strata.errors import UnresolvedDependency, DependencyCycle


class TriviallyMissingLayer(Layer):
    def var_a(self, nope):
        return 'a'


def test_trivially_missing():
    layers = [TriviallyMissingLayer]
    variables = ez_vars(layers)
    try:
        ConfigSpec(variables, layers)
    except Exception as e:
        assert type(e) is UnresolvedDependency
        return
    assert False, 'should have raised an UnresolvedDependency'


def test_unmeetable_requirements():
    class OKLayer(Layer):
        def var_a(self):
            return 'a'

        def var_b(self, var_a):
            return 'b'

    class UnprovidedVariable(Variable):
        pass

    layers = [OKLayer]
    variables = ez_vars(layers) + [UnprovidedVariable]
    try:
        ConfigSpec(variables, layers)
    except Exception as e:
        assert type(e) is UnresolvedDependency
        return
    assert False, 'should have raised an UnresolvedDependency'


def test_direct_dep_cycle():
    class CycleLayer(Layer):
        def var_a(self, var_a):
            return None
    layers = [CycleLayer]
    try:
        ConfigSpec(ez_vars(layers), layers)
    except Exception as e:
        assert type(e) is DependencyCycle
        return
    assert False, 'should have raised a DependencyCycle'


def test_indirect_dep_cycle():
    class CycleLayer(Layer):
        def var_a(self):
            pass

        def var_b(self, var_a, var_c):
            pass

        def var_c(self, var_b):
            pass

    layers = [CycleLayer]
    try:
        ConfigSpec(ez_vars(layers), layers)
    except Exception as e:
        assert type(e) is DependencyCycle
        return
    assert False, 'should have raised a DependencyCycle'
