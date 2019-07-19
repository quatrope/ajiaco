#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of the
#   Ajiaco Project (https://github.com/leliel12/ajiaco/).
# Copyright (c) 2018-2019, Juan B Cabral
# License: BSD-3-Clause
#   Full Text: https://github.com/leliel12/ajiaco/blob/master/LICENSE


# =============================================================================
# DOCS
# =============================================================================

"""This file is for distribute ajiaco

"""


# =============================================================================
# IMPORTS
# =============================================================================

import os

from ez_setup import use_setuptools
use_setuptools()

from setuptools import setup, find_packages

os.environ["__AJIACO_SETUP__"] = "True"
import ajiaco as ajc


# =============================================================================
# CONSTANTS
# =============================================================================

REQUIREMENTS = [
    # "tornado",  # the webserver and dispatcher

    "sqlalchemy",  # the database
    "sqlalchemy-utils",  # utilities for manipulate the database

    # "wtforms-tornado",  # using forms with the request data of tornado

    # "jinja2",  # the templates engine
    # "tzlocal",  # date time and time zone manipulations
    # "passlib",  # for password encription
    "shortuuid",  # short random unique id

    # "tabulate",  # helpful tabular formated for cli
    "colored-traceback", "colorama",  # add colors to the console
    # "wtforms",  # form manage user input

    # "pip",  # this is for acces information about the installed packages
]


# =============================================================================
# FUNCTIONS
# =============================================================================

def do_setup():
    setup(
        name=ajc.NAME,
        version=ajc.VERSION,
        description=ajc.DOC,
        author=ajc.AUTHORS,
        author_email=ajc.EMAIL,
        url=ajc.URL,
        license=ajc.LICENSE,
        keywords=ajc.KEYWORDS,
        classifiers=(
            "Development Status :: 4 - Beta",
            "Intended Audience :: Education",
            "Intended Audience :: Science/Research",
            "License :: OSI Approved :: BSD License",
            "Operating System :: OS Independent",
            "Programming Language :: Python",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: Implementation :: CPython",
            "Topic :: Internet :: WWW/HTTP",
            "Topic :: Internet :: WWW/HTTP :: Dynamic Content"
            "Topic :: Scientific/Engineering"),
        packages=[
            pkg for pkg in find_packages() if pkg.startswith("ajiaco")],
        py_modules=["ez_setup"],
        # entry_points = {
        #     'console_scripts': ['mkajc=ajiaco.create:mkajc'],
        # },
        install_requires=REQUIREMENTS)


if __name__ == "__main__":
    do_setup()
