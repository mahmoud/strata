# -*- coding: utf-8 -*-

from strata import Variable, Layer, ConfigSpec
from strata.validators import Integer, Float


class TestVariable(Variable):
    """
    A test variable to test out various validators
    """
    validator = None


class TestLayer(Layer):
    test_value = None

    def test_variable(self):
        return self.test_value


TEST_CSPEC = ConfigSpec([TestVariable], [TestLayer])
TestConfig = TEST_CSPEC.make_config(name='TestConfig')


def _do_value_test(value, expected, validator):
    TestLayer.test_value = value
    TestVariable.validator = validator
    test_config = TestConfig(_defer=True)
    try:
        test_config._process()
    except Exception as e:
        assert isinstance(e, ValueError)
        return
    assert test_config.test_variable == expected


def test_integer():
    _do_value_test(5, 5, Integer(min_val=5))
    _do_value_test('5', 5, Integer(max_val=5))
    _do_value_test('0', 0, Integer())
    _do_value_test('0', 0, int)


def test_float():
    _do_value_test(5.0, 5.0, Float(min_val=5, max_val=5))
    _do_value_test(3.1415, 3.14, Float(ndigits=2))
