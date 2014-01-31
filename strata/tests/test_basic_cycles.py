# -*- coding: utf-8 -*-

from strata import Layer, LayerSet, ConfigSpec
from strata.core import ez_vars  # TODO
from strata.config import DependencyCycle


class SelfCycleLayer(Layer):
    "Provides a variable that depends on itself"
    def var_a(self, var_a):
        return 'a'


class SelfMutualCycleLayer(Layer):
    "A Layer providing two variables each of which depend on one another."
    def var_d(self, var_e):
        return 'd'

    def var_e(self, var_d):
        return 'e'


class MutualCycleLayerOne(Layer):
    "Half of a pair of Layers make up a cycle"
    def var_b(self, var_c):
        return 'b'


class MutualCycleLayerTwo(Layer):
    def var_c(self, var_b):
        return 'c'


def test_self_cycle():
    layerset = LayerSet('default', [SelfCycleLayer])
    variables = ez_vars(layerset)
    try:
        ConfigSpec(variables, layerset)
    except Exception as e:
        assert type(e) is DependencyCycle
        return
    assert False, 'should have raise a DependencyCycle'


def test_self_mutual_cycle():
    layerset = LayerSet('default', [SelfMutualCycleLayer])
    variables = ez_vars(layerset)
    try:
        ConfigSpec(variables, layerset)
    except Exception as e:
        assert type(e) is DependencyCycle
        return
    assert False, 'should have raise a DependencyCycle'


def test_mutual_cycle():
    layerset = LayerSet('default', [MutualCycleLayerOne, MutualCycleLayerTwo])
    variables = ez_vars(layerset)
    try:
        ConfigSpec(variables, layerset)
    except Exception as e:
        assert type(e) is DependencyCycle
        return
    assert False, 'should have raise a DependencyCycle'


def test_masking_self_cycle():
    "Try to mask a dependency cycle by providing the variable earlier"
    class MaskingLayer(Layer):
        def var_a(self):  # no deps
            return 'masked a'

    layerset = LayerSet('default', [SelfCycleLayer])
    variables = ez_vars(layerset)
    try:
        ConfigSpec(variables, layerset)
    except Exception as e:
        assert type(e) is DependencyCycle
        return
    assert False, 'should have raise a DependencyCycle'
