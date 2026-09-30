
import pytest

from strata import Layer, ConfigSpec
from strata.core import ez_vars  # TODO
from strata.errors import DependencyCycle


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
    layers = [SelfCycleLayer]
    variables = ez_vars(layers)
    with pytest.raises(DependencyCycle) as exc_info:
        ConfigSpec(variables, layers)
    assert exc_info.type is DependencyCycle


def test_self_mutual_cycle():
    layerset = [SelfMutualCycleLayer]
    variables = ez_vars(layerset)
    with pytest.raises(DependencyCycle) as exc_info:
        ConfigSpec(variables, layerset)
    assert exc_info.type is DependencyCycle


def test_mutual_cycle():
    layers = [MutualCycleLayerOne, MutualCycleLayerTwo]
    variables = ez_vars(layers)
    with pytest.raises(DependencyCycle) as exc_info:
        ConfigSpec(variables, layers)
    assert exc_info.type is DependencyCycle


def test_masking_self_cycle():
    "Try to mask a dependency cycle by providing the variable earlier"
    class MaskingLayer(Layer):
        def var_a(self):  # no deps
            return 'masked a'

    layers = [MaskingLayer, SelfCycleLayer]
    variables = ez_vars(layers)
    with pytest.raises(DependencyCycle) as exc_info:
        ConfigSpec(variables, layers)
    assert exc_info.type is DependencyCycle
