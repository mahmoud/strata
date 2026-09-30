import pytest

from strata import Variable, Layer, ConfigSpec
from strata.core import autoprovide, ez_vars
from strata.utils import get_arg_names, inject


def test_variable_naming():
    class DatabaseURL(Variable):
        "Where the database lives."

    assert DatabaseURL.name == 'database_url'
    assert DatabaseURL.description == 'Where the database lives.'
    assert DatabaseURL.summary == 'Where the database lives.'

    class Explicit(Variable):
        name = 'other_name'
        summary = 'short'

    assert Explicit.name == 'other_name'
    assert Explicit.summary == 'short'

    with pytest.raises(TypeError) as exc_info:
        class Hidden(Variable):
            name = '_hidden'
    assert 'underscore' in str(exc_info.value)


def test_ez_vars():
    class L(Layer):
        def var_a(self):
            return 1

        def _private(self):
            return 2

    names = [v.name for v in ez_vars([L])]
    assert 'var_a' in names
    assert '_private' not in names


def test_autoprovide_decorator_and_explicit_variable():
    class BuildInfo(Variable):
        "Build metadata."

    class MetaLayer(Layer):
        _autoprovided = [BuildInfo, 'hostname']

        def build_info(self):
            return {'sha': 'abc'}

        def hostname(self):
            return 'box'

        @autoprovide(summary='seconds since start', validator=int)
        def uptime(self):
            "How long we have been up."
            return '42'

        @autoprovide
        def plain(self):
            return 'plain'

    class Report(Variable):
        pass

    class ReportLayer(Layer):
        def report(self, build_info, hostname, uptime, plain):
            return f"{build_info['sha']}@{hostname} up {uptime!r} {plain}"

    spec = ConfigSpec([Report], [MetaLayer, ReportLayer])
    ap_names = sorted(v.name for v in spec._autoprovided_variables)
    assert ap_names == ['build_info', 'config', 'hostname', 'plain', 'uptime']
    uptime_var = spec.name_var_map['uptime']
    assert uptime_var.summary == 'seconds since start'
    assert uptime_var.description == 'How long we have been up.'

    conf = spec.make_config()()
    assert conf.report == "abc@box up 42 plain"  # validator=int applied
    assert conf.uptime == 42


def test_autoprovide_errors():
    with pytest.raises(TypeError):
        autoprovide(nope=1)

    with pytest.raises(TypeError):
        autoprovide('not a function')

    class BadTypes(Layer):
        _autoprovided = [42]

    with pytest.raises(TypeError) as exc_info:
        ConfigSpec([], [BadTypes])
    assert 'unsupported autoprovide types' in str(exc_info.value)

    class Unresolvable(Layer):
        _autoprovided = ['no_such_method']

    with pytest.raises(TypeError) as exc_info:
        ConfigSpec([], [Unresolvable])
    assert 'unable to resolve' in str(exc_info.value)


def test_get_arg_names_and_inject():
    def f(a, b=2, *args, kw_only=3, **kwargs):
        return a, b, kw_only, kwargs

    assert get_arg_names(f) == ('a', 'b')
    assert get_arg_names(f, only_required=True) == ('a',)
    assert inject(f, {'a': 1, 'extra': 9}) == (1, 2, 3, {'extra': 9})

    def g(a, b=2):
        return a, b

    assert inject(g, {'a': 1, 'b': 5, 'extra': 9}) == (1, 5)

    with pytest.raises(TypeError):
        get_arg_names(42)
