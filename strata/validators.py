# -*- coding: utf-8 -*-

import os

from .fileutils import FilePerms

# TODO: should validators also get a copy of the Variable?


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
    #  * owner/group
    def __init__(self, should_exist=None, min_perms=None):
        self.should_exist = should_exist
        if min_perms is not None:
            # TODO: check for integer
            min_perms = FilePerms.from_int(min_perms)
        self.min_perms = min_perms

    def validate(self, value):
        # check for valid path
        does_exist = os.path.exists(value)
        if self.should_exist is not None:
            if does_exist != self.should_exist:
                raise ValueError('expected %r exists = %r'
                                 % (value, self.should_exist))
        if does_exist and self.min_perms is not None:
            # TODO: can check for creatable with the perms specified
            file_mode = os.lstat(value).st_mode
            file_perms = FilePerms.from_int(file_mode)
            file_perms_int = int(file_perms)  # TODO: operator overload this?
            min_perms_int = int(self.min_perms)
            if not file_perms_int == (file_perms_int | min_perms_int):
                raise ValueError('minimum file permissions not met: file %r'
                                 ' is %o, expected at least %o'
                                 % (value, file_perms_int, min_perms_int))
        return value


class URL(Validator):
    pass


class LocalPort(Validator):
    pass  # check for openability? probably too heavy/nuanced
