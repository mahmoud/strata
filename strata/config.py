# -*- coding: utf-8 -*-

from core import _KNOWN_VARS

_ENV_LAYERS_MAP = {'dev': []}


def detect_env():
    # TODO
    return 'dev'


class Config(object):
    def __init__(self, **kwargs):
        self.env = kwargs.pop('env', None)
        if self.env is None:
            self.env = detect_env()  # TODO: member function?
        self._layer_types = _ENV_LAYERS_MAP[self.env]  # TODO
        self._layers = [t() for t in self._layer_types]

        self.deps = {}
        self.results = {}
        self.known_vars = _KNOWN_VARS.keys()  # TODO: ?

        self._build_graph()
        self._process()

    def _build_graph(self):
        # TODO: topological sort
        pass

    def _process(self):
        pass
