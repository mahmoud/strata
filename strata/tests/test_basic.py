# -*- coding: utf-8 -*-

from pprint import pprint

import common
from strata.core import Layer
from strata.config import ConfigSpec

from strata.core import ez_vars  # tmp


class FirstLayer(Layer):
    #def __init__(self, stuff):  # TODO: support injecting kwargs here?
    #    self.stuff = stuff

    def var_a(self):
        return 0

    def var_b(self, var_a):
        if var_a:
            return 1
        else:
            raise KeyError('nope')

    def var_c(self):
        return 3

    def var_f(self, var_e):
        return 6


class SecondLayer(Layer):
    def var_b(self):
        return 2

    def var_d(self, var_b, var_c):
        return 4


class ThirdLayer(Layer):
    def var_a(self, var_e):
        assert False, 'var_a should have been provided by FirstLayer'

    def var_e(self):
        return -1


BASIC_LAYERS = [FirstLayer, SecondLayer, ThirdLayer]


def get_basic_config_spec(layers=BASIC_LAYERS):
    variables = ez_vars(BASIC_LAYERS)
    cspec = ConfigSpec(variables, layers)
    return cspec


def get_basic_config(req_var_names=None, cspec=None):
    req_var_names = set(req_var_names or ['var_d'])
    cspec = cspec or get_basic_config_spec()
    req_vars = [v for v in cspec.variables if v.name in req_var_names]
    return cspec.make_config(reqs=req_vars)


def test_basic_vars():
    conf_type = get_basic_config()
    conf = conf_type()
    res = conf.results
    expected_keys = set(['var_a', 'var_b', 'var_c', 'var_d', 'config'])
    assert set(res.keys()) == expected_keys
    assert all([v >= 0 for v in res.values()])
    assert res['var_a'] == 0
    assert res['var_b'] == 2
    assert res['var_c'] == 3
    assert res['var_d'] == 4
    pprint(conf.results)
    return conf


if __name__ == '__main__':
    test_basic_vars()
