# Copyright (c) 2021 Siphon Contributors.
# Distributed under the terms of the BSD 3-Clause License.
# SPDX-License-Identifier: BSD-3-Clause
"""Tools for versioning."""


def get_version():
    """Get Siphon's version.

    Either get it from package metadata, or get it using version control information if
    a development install.
    """
    try:
        from setuptools_scm import get_version as _get_version
        return _get_version(root='../..', relative_to=__file__,
                            version_scheme='post-release')
    except (ImportError, LookupError):
        from importlib.metadata import PackageNotFoundError, version

        try:
            return version(__package__)
        except PackageNotFoundError:
            return 'Unknown'
