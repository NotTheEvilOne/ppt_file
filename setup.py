# -*- coding: utf-8 -*-

"""
file.py
Working with a file abstraction layer
----------------------------------------------------------------------------
(C) direct Netware Group - All rights reserved
https://www.direct-netware.de/redirect?py;file

This Source Code Form is subject to the terms of the Mozilla Public License,
v. 2.0. If a copy of the MPL was not distributed with this file, You can
obtain one at http://mozilla.org/MPL/2.0/.
----------------------------------------------------------------------------
https://www.direct-netware.de/redirect?licenses;mpl2
----------------------------------------------------------------------------
setup.py
"""

from os import makedirs, path

try:
    from setuptools import find_packages, setup
except ImportError:
    from distutils import find_packages, setup
#

_use_dist_mode = False

try:
    from dNG.distutils.command.build_py import BuildPy
    from dNG.distutils.command.sdist import Sdist
    from dNG.distutils.temporary_directory import TemporaryDirectory
except ImportError:
    _use_dist_mode = True
#

def get_version():
    """
Returns the version currently in development.

:return: (str) Version string
:since:  v0.1.1
    """

    return "v1.0.0"
#

_setup = { "name": "dng-file",
           "version": get_version()[1:],
           "description": "Working with a file abstraction layer",
           "long_description": "The file.py abstraction layer provides an interface similar to FileIO with support for read, lock and write timeouts.",
           "author": "direct Netware Group et al.",
           "author_email": "web@direct-netware.de",
           "license": "MPL2",
           "url": "https://www.direct-netware.de/redirect?py;file",

           "platforms": [ "any" ],

           "data_files": [ ( "docs", [ "LICENSE", "README" ]) ]
          }

if (_use_dist_mode):
    _setup['package_dir'] = { "": "src" }
    _setup['packages'] = find_packages("src")

    setup(**_setup)
else:
    with TemporaryDirectory(dir = ".") as build_directory:
        parameters = { "pyFileVersion": get_version() }

        BuildPy.set_build_target_path(build_directory)
        BuildPy.set_build_target_parameters(parameters)

        Sdist.set_build_target_path(build_directory)
        Sdist.set_build_target_parameters(parameters)

        makedirs(path.join(build_directory, "src", "dNG"))

        _setup['packages'] = [ "dNG" ]

        # Customize "cmdclass" to first run builder.py
        _setup['cmdclass'] = { "build_py": BuildPy, "sdist": Sdist }

        setup(**_setup)
    #
#
