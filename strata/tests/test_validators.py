import os
import sys

import pytest

from strata.validators import Integer, Float, Boolean, Choice, List, FilePath


def test_integer_bounds():
    assert Integer()('7') == 7
    assert Integer(min_val=1)(1) == 1
    with pytest.raises(ValueError):
        Integer(min_val=1)(0)
    with pytest.raises(ValueError):
        Integer(max_val=10)(11)
    with pytest.raises(ValueError):
        Integer()('seven')


def test_float_bounds_and_rounding():
    assert Float(ndigits=2)(3.14159) == 3.14
    with pytest.raises(ValueError):
        Float(min_val=0.5)(0.25)
    with pytest.raises(ValueError):
        Float(max_val=0.5)(0.75)


def test_boolean_strict_and_lenient():
    assert Boolean()(True) is True
    with pytest.raises(ValueError):
        Boolean()('true')
    lenient = Boolean(strict=False)
    assert lenient(' YES ') is True
    assert lenient('off') is False
    assert lenient(False) is False
    with pytest.raises(ValueError):
        lenient('maybe')
    with pytest.raises(ValueError):
        lenient(1)  # only bools and (lenient) strings


def test_choice():
    color = Choice(['red', 'green'])
    assert color('red') == 'red'
    with pytest.raises(ValueError) as exc_info:
        color('blue')
    assert "'blue'" in str(exc_info.value)
    port = Choice([80, 443], item_type=int)
    assert port('443') == 443  # coerced before the membership check


def test_list():
    assert List(item_type=int)(['1', '2']) == [1, 2]
    assert List(item_type=int, list_type=tuple)('12') == (1, 2)
    assert List()(['a', 1]) == ['a', 1]  # default item validator is identity


def test_file_path(tmp_path):
    path = tmp_path / 'f.txt'
    path.write_text('x')
    os.chmod(path, 0o640)

    assert FilePath()(str(path)) == str(path)
    assert FilePath(should_exist=True)(str(path)) == str(path)
    with pytest.raises(ValueError):
        FilePath(should_exist=False)(str(path))
    with pytest.raises(ValueError):
        FilePath(should_exist=True)(str(tmp_path / 'missing'))
    # a missing file with should_exist unset passes; nothing to check perms on
    assert FilePath(min_perms=0o644)(str(tmp_path / 'missing'))

    assert FilePath(min_perms=0o640)(str(path)) == str(path)
    assert FilePath(min_perms=0o600)(str(path)) == str(path)
    if sys.platform == 'win32':
        return  # chmod cannot remove group/other read bits on Windows
    with pytest.raises(ValueError) as exc_info:
        FilePath(min_perms=0o644)(str(path))
    assert 'minimum file permissions not met' in str(exc_info.value)
