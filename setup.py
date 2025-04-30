# -*- coding: utf-8 -*-

"""
Personal Python Toolkit
Modularized all-in-one toolkit for Python
----------------------------------------------------------------------------
(C) Tobias "NotTheEvilOne" Wolf - All rights reserved
https://github.com/NotTheEvilOne/ppt_file

This Source Code Form is subject to the terms of the Mozilla Public License,
v. 2.0. If a copy of the MPL was not distributed with this file, You can
obtain one at http://mozilla.org/MPL/2.0/.
"""

import os
from typing import Dict, Any

try:
    from setuptools import find_packages, setup
except ImportError:
    from distutils import find_packages, setup  # type: ignore[attr-defined, unused-ignore]


def get_version() -> str:
    """
    Returns the version currently in development.

    :return: (str) Version string
    :since:  v0.0.1
    """

    return os.environ.get("PPT_VERSION", "0.0.0.dev1")


_setup: Dict[str, Any] = {
    "version": get_version(),
    "data_files": [("docs", ["LICENSE", "README"])],
}

_setup["package_dir"] = {"": "src"}
_setup["packages"] = find_packages("src")

setup(**_setup)
