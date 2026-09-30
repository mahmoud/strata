
from strata import Variable, Layer, ConfigSpec
from strata.validators import Integer, Float


class SampleVariable(Variable):
    """
    A test variable to test out various validators
    """
    validator = None


class SampleLayer(Layer):
    test_value = None

    def sample_variable(self):
        return self.test_value


SAMPLE_CSPEC = ConfigSpec([SampleVariable], [SampleLayer])
SampleConfig = SAMPLE_CSPEC.make_config(name='SampleConfig')


def _do_value_test(value, expected, validator):
    SampleLayer.test_value = value
    SampleVariable.validator = validator
    test_config = SampleConfig(_defer=True)
    try:
        test_config._process()
    except Exception as e:
        assert isinstance(e, ValueError)
        return
    assert test_config.sample_variable == expected


def test_integer():
    _do_value_test(5, 5, Integer(min_val=5))
    _do_value_test('5', 5, Integer(max_val=5))
    _do_value_test('0', 0, Integer())
    _do_value_test('0', 0, int)


def test_float():
    _do_value_test(5.0, 5.0, Float(min_val=5, max_val=5))
    _do_value_test(3.1415, 3.14, Float(ndigits=2))
