# Copyright (c) 2013-2021 Siphon Contributors.
# Distributed under the terms of the BSD 3-Clause License.
# SPDX-License-Identifier: BSD-3-Clause
"""Tools for accessing atmospheric and oceanic science data on remote servers."""

# Version import needs to come first so everyone else can pull on import
from ._version import get_version

__version__ = get_version()
del get_version
