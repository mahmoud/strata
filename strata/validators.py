
import os

from boltons.fileutils import FilePerms

# TODO: should validators also get a copy of the Variable?


class Validator:
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
    _true_strs = ('true', 'yes', 'on', '1')
    _false_strs = ('false', 'no', 'off', '0')

    def __init__(self, strict=True):
        # non-strict accepts case-insensitive strings (env vars, CLI, TOML)
        self.strict = strict

    def validate(self, value):
        if isinstance(value, bool):
            return value
        if not self.strict and isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in self._true_strs:
                return True
            if lowered in self._false_strs:
                return False
        raise ValueError('expected a boolean, not %r' % (value,))


class Choice(Validator):
    def __init__(self, choices, item_type=None):
        self.choices = list(choices)
        self.item_type = item_type

    def validate(self, value):
        if self.item_type is not None:
            value = self.item_type(value)
        if value not in self.choices:
            raise ValueError('expected one of %r, not %r' % (self.choices, value))
        return value


class List(Validator):
    def __init__(self, item_type=None, list_type=None):
        self.item_type = item_type or Validator()
        assert callable(self.item_type)
        self.list_type = list_type or list

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
