# -*- coding: utf-8 -*-

from pprint import pprint

from strata.core import Layer, LayerSet
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


BASIC_LAYERSET = LayerSet('default', [FirstLayer, SecondLayer, ThirdLayer])


def get_basic_config_spec(layerset=BASIC_LAYERSET):
    assert repr(layerset)
    assert list(layerset)
    assert layerset[0] is FirstLayer
    variables = ez_vars(layerset)
    cspec = ConfigSpec(variables, layerset)
    return cspec


def get_basic_config(req_var_names=None, cspec=None):
    cspec = cspec or get_basic_config_spec()
    return cspec.make_config()


def test_basic_vars():
    conf_type = get_basic_config()
    conf = conf_type()
    res = conf._result_map
    expected_keys = set(['var_a', 'var_b', 'var_e',
                         'var_c', 'var_d', 'config'])
    assert set(res.keys()) > expected_keys
    assert res['var_a'] == 0
    assert res['var_b'] == 2
    assert res['var_c'] == 3
    assert res['var_d'] == 4
    assert res['var_e'] == -1
    pprint(conf)
    return conf


if __name__ == '__main__':
    test_basic_vars()
