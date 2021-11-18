# Copyright (c) 2013-2015 Siphon Contributors.
# Distributed under the terms of the BSD 3-Clause License.
# SPDX-License-Identifier: BSD-3-Clause
"""Setup script for installing Siphon."""
import sys

from setuptools import setup


if sys.version_info[0] < 3:
    error = """
    Siphon greater than 0.9 requires Python 3.7 or above.
    If you're using Python 2.7, please install Siphon v0.9.0,
    which is the last release that supports Python 2.7,
    though it is no longer maintained.

    Python {py} detected.
    """.format(py='.'.join([str(v) for v in sys.version_info[:3]]))

    print(error)  # noqa: T001
    sys.exit(1)

setup(use_scm_version={'version_scheme': 'post-release'})
