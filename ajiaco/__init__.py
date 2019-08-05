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

"""Ajiaco easy social science experiments in a web environment"""


# =============================================================================
# CONSTANTS
# =============================================================================

__version__ = ("0", "1")

NAME = "ajiaco"

DOC = __doc__

VERSION = ".".join(__version__)

AUTHORS = "Juan Cabral"

EMAIL = "jbc.develop@gmail.com"

URL = "http://ajiaco.org/"

LICENSE = "BSD-3-Clause"

KEYWORDS = "social-science".split()


# =============================================================================
# IMPORTS
# =============================================================================

import os

if not os.getenv("__AJIACO_SETUP__"):
    import colored_traceback
    colored_traceback.add_hook()

del os
