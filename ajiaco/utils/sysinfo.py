#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime as dt
import platform
from subprocess import check_output
import sys
import tzlocal


# =============================================================================
# FUNCTIONS
# =============================================================================


def utcnow():
    return dt.datetime.now(dt.timezone.utc)


def pip_freeze():
    out = check_output(["pip", "freeze", "--disable-pip-version-check"])
    return out.decode("utf8").splitlines()


def info_dict():
    """Return a dictiornary that represent the status of the environment.
    This value is stored when the database is created.

    """
    return {
        "PY_PKGS": pip_freeze(),
        "PLATFORM": platform.platform(),
        "SYSTEM_ENCODING": sys.getfilesystemencoding(),
        "SYSTEM_TIME_ZONE": tzlocal.get_localzone_name(),
        "UTC_CREATED_AT": utcnow().isoformat(),
    }
