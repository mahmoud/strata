import inspect


def get_arg_names(f, only_required=False):
    """Positional parameter names of *f*; bound methods drop ``self``."""
    try:
        sig = inspect.signature(f)
    except (TypeError, ValueError) as e:
        raise TypeError(f'unsupported provider callable: {f!r}') from e
    names = []
    for p in sig.parameters.values():
        if p.kind not in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD):
            continue
        if only_required and p.default is not p.empty:
            continue
        names.append(p.name)
    return tuple(names)


def inject(f, injectables):
    """Call *f* with the subset of *injectables* its parameters name."""
    sig = inspect.signature(f)
    accepts_kwargs = any(p.kind is p.VAR_KEYWORD for p in sig.parameters.values())
    if accepts_kwargs:
        return f(**injectables)
    kwargs = {k: v for k, v in injectables.items() if k in sig.parameters}
    return f(**kwargs)
