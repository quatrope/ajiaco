#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of the
#   Ajiaco Project (https://github.com/quatrope/ajiaco/).
# Copyright (c) 2018-2019, Juan B Cabral
# License: BSD-3-Clause
#   Full Text: https://github.com/quatrope/ajiaco/blob/master/LICENSE


# =============================================================================
# DOCS
# =============================================================================

"""Here is all the utilities classes of Ajiaco"""


# =============================================================================
# IMPORTS
# =============================================================================

from collections.abc import MutableMapping


# =============================================================================
# BUNCH inspired from scikit-learn
# =============================================================================

class Bunch(MutableMapping):
    """Dict-like object that exposes its keys as attributes.

    >>> b = Bunch(a=1, b=2)
    >>> b['b']
    2
    >>> b.b
    2
    >>> b.a = 3
    >>> b['a']
    3
    >>> b.c = 6
    >>> b['c']
    6

    """

    def __init__(self, bunch_name, **kwargs):
        super().__setattr__("_bunch_name", bunch_name)
        super().__setattr__("_d", kwargs)

    def __repr__(self):
        keys = ", ".join(self._d.keys())
        return f"{self._bunch_name}({keys})"

    def __dir__(self):
        return list(self._d.keys())

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(key)

    def __setattr__(self, key, value):
        self._d[key] = value

    def __delitem__(self, key):
        del self._d[key]

    def __setitem__(self, key, value):
        self._d[key] = value

    def __getitem__(self, key):
        return self._d[key]

    def __iter__(self):
        return iter(self._d)

    def __len__(self):
        return len(self._d)

    @property
    def bunch_name(self):
        """The name of this bunch"""
        return self._bunch_name
