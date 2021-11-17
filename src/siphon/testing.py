# Copyright (c) 2013-2015 Siphon Contributors.
# Distributed under the terms of the BSD 3-Clause License.
# SPDX-License-Identifier: BSD-3-Clause
"""Utilities for testing siphon."""

import os.path

import vcr


def get_recorder(test_file_path):
    """Return an appropriate response recorder for the given path."""
    return vcr.VCR(cassette_library_dir=os.path.join(os.path.dirname(test_file_path),
                                                     'fixtures'))
