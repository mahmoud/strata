# -*- coding: utf-8 -*-

import os


class Validator(object):
    def validate(self, value):
        "implement me"
        return value

    def __call__(self, value):
        return self.validate(value)


class Text(Validator):
    pass


class Bytes(Validator):
    pass


class Integer(Validator):
    # TODO: strict.  strict only coerces from string, expects an int
    # in all other occasions or perhaps only complains on floats.
    def __init__(self, min_val=None, max_val=None):
        self.min_val = min_val
        self.max_val = max_val

    def validate(self, value):
        ret = int(value)
        if self.min_val is not None:
            if ret < self.min_val:
                raise ValueError()
        if self.max_val is not None:
            if ret > self.max_val:
                raise ValueError()
        return ret


class Float(Validator):
    def __init__(self, min_val=None, max_val=None, ndigits=None):
        self.min_val = min_val
        self.max_val = max_val
        self.ndigits = ndigits
        if ndigits is not None:
            round(0.0, self.ndigits)  # sanity check ndigits

    def validate(self, value):
        ret = float(value)
        if self.ndigits is not None:
            ret = round(value, self.ndigits)
        if self.min_val is not None:
            if ret < self.min_val:
                raise ValueError()
        if self.max_val is not None:
            if ret > self.max_val:
                raise ValueError()
        return ret


class Boolean(Validator):
    def __init__(self, strict=True):
        pass
    # non-strict can accept case-insensitive strings


class Choice(Validator):
    def __init__(self, choices=None, item_type=None):
        self.choices = choices
        self.item_type = item_type


class List(Validator):
    def __init__(self, item_type=None, list_type=None):
        item_type = item_type or Validator
        assert callable(item_type)
        list_type = list_type or list

    def validate(self, value):
        return self.list_type([self.item_type(x) for x in value])


class FilePath(Validator):
    # TODO
    #  * type? (dir/file/symlink)
    #  * size?
    #  * absolutify/relativize?
    def __init__(self, exists=None, readable=None, writable=None,
                 executable=None):
        self.want_exists = exists
        self.want_readable = readable
        self.want_writable = writable
        self.want_executable = executable

    def validate(self, value):
        if self.want_exists is not None:
            if os.path.exists(value) != self.want_exists:
                raise ValueError('expected %r exists = %r'
                                 % (value, self.want_exists))
        # etc.


class URL(Validator):
    pass


class LocalPort(Validator):
    pass  # check for openability
