# -*- coding: utf-8 -*-

import os


class Validator(object):
    def validate(self, value):
        "implement me"
        return value

    def __call__(self, value):
        return self.validate(value)


class Text(Validator):
    def validate(self, value):
        pass


class Bytes(Validator):
    pass


class Integer(Validator):
    pass


class Float(Validator):
    pass


class Boolean(Validator):
    def __init__(self, strict=True):
        pass

    # non-strict can accept case-insensitive strings


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
