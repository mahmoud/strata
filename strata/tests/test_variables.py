# -*- coding: utf-8 -*-

from strata import Variable, Layer, ConfigSpec
from strata.validators import Integer


class TestVariable(Variable):
    """
    A test variable to test out various validators
    """
    validator = None


class TestLayer(Layer):
    test_value = None

    def test_variable(self):
        return self.test_value


def test_integer():
    cspec = ConfigSpec([TestVariable], [TestLayer])
    TestConfig = cspec.make_config(name='TestConfig')
    TestLayer.test_value = 'hello'
    TestVariable.validator = Integer()
    test_config = TestConfig()

    assert test_config.test_variable == 5
