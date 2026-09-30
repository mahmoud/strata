
import pytest

from strata import Layer, ConfigSpec, Variable
from strata.core import ez_vars  # TODO
from strata.errors import UnresolvedDependency, DependencyCycle


class TriviallyMissingLayer(Layer):
    def var_a(self, nope):
        return 'a'


def test_trivially_missing():
    layers = [TriviallyMissingLayer]
    variables = ez_vars(layers)
    with pytest.raises(UnresolvedDependency) as exc_info:
        ConfigSpec(variables, layers)
    assert exc_info.type is UnresolvedDependency


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
    with pytest.raises(UnresolvedDependency) as exc_info:
        ConfigSpec(variables, layers)
    assert exc_info.type is UnresolvedDependency


def test_direct_dep_cycle():
    class CycleLayer(Layer):
        def var_a(self, var_a):
            return None
    layers = [CycleLayer]
    with pytest.raises(DependencyCycle) as exc_info:
        ConfigSpec(ez_vars(layers), layers)
    assert exc_info.type is DependencyCycle


def test_indirect_dep_cycle():
    class CycleLayer(Layer):
        def var_a(self):
            pass

        def var_b(self, var_a, var_c):
            pass

        def var_c(self, var_b):
            pass

    layers = [CycleLayer]
    with pytest.raises(DependencyCycle) as exc_info:
        ConfigSpec(ez_vars(layers), layers)
    assert exc_info.type is DependencyCycle
