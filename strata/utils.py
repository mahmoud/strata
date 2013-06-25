# -*- coding: utf-8 -*-

import re
import types
import inspect
from inspect import ArgSpec

# TODO: use boltons

_camel2under_re = re.compile('((?<=[a-z0-9])[A-Z]|(?!^)[A-Z](?=[a-z]))')


def camel2under(string):
    return _camel2under_re.sub(r'_\1', string).lower()


def under2camel(string):
    return ''.join(w.capitalize() or '_' for w in string.split('_'))


def getargspec(f):
    # TODO: support partials
    if not inspect.isfunction(f) and not inspect.ismethod(f) \
            and hasattr(f, '__call__'):
        f = f.__call__  # callable objects

    if isinstance(getattr(f, '_argspec', None), ArgSpec):
        return f._argspec  # we'll take your word for it; good luck, lil buddy.

    ret = inspect.getargspec(f)

    if not all([isinstance(a, basestring) for a in ret.args]):
        raise TypeError('does not support anonymous tuple arguments '
                        'or any other strange args for that matter.')
    if isinstance(f, types.MethodType):
        ret = ret._replace(args=ret.args[1:])  # throw away "self"
    return ret


def get_arg_names(f, only_required=False):
    arg_names, _, _, defaults = getargspec(f)

    if only_required and defaults:
        arg_names = arg_names[:-len(defaults)]

    return tuple(arg_names)


def inject(f, injectables):
    arg_names, _, kw_name, defaults = getargspec(f)
    defaults = dict(reversed(zip(reversed(arg_names),
                                 reversed(defaults or []))))
    all_kwargs = dict(defaults)
    all_kwargs.update(injectables)
    if kw_name:
        return f(**all_kwargs)

    kwargs = dict([(k, v) for k, v in all_kwargs.items() if k in arg_names])
    return f(**kwargs)
