# -*- coding: utf-8 -*-

from strata import Layer, ConfigSpec, Variable
from strata.core import ez_vars  # TODO
from strata.config import UnresolvedDependency


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
    variables = ez_vars(layers)
    cspec = ConfigSpec(variables, layers)
    try:
        cspec.make_config(reqs=[UnprovidedVariable])
    except Exception as e:
        assert type(e) is UnresolvedDependency
        return
    assert False, 'should have raised an UnresolvedDependency'
