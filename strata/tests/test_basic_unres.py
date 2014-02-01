# -*- coding: utf-8 -*-

from strata import Layer, LayerSet, ConfigSpec, Variable
from strata.core import ez_vars  # TODO
from strata.config import UnresolvedDependency


class TriviallyMissingLayer(Layer):
    def var_a(self, nope):
        return 'a'


def test_trivially_missing():
    layerset = LayerSet('default', [TriviallyMissingLayer])
    variables = ez_vars(layerset)
    try:
        ConfigSpec(variables, layerset)
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

    layerset = LayerSet('default', [OKLayer])
    variables = ez_vars(layerset)
    cspec = ConfigSpec(variables, layerset)
    try:
        cspec.make_config(reqs=[UnprovidedVariable])
    except Exception as e:
        assert type(e) is UnresolvedDependency
        return
    assert False, 'should have raised an UnresolvedDependency'
