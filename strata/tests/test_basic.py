# -*- coding: utf-8 -*-

from strata.core import Variable, Layer, Config


class VarA(Variable):
    pass


class VarB(Variable):
    pass


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


class SecondLayer(Layer):
    def var_b(self):
        return 2
