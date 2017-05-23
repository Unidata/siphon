# Copyright (c) 2013-2015 University Corporation for Atmospheric Research/Unidata.
# Distributed under the terms of the MIT License.
# SPDX-License-Identifier: MIT
"""Utilities for testing siphon."""

import os.path

import vcr


def get_recorder(test_file_path):
    """Return an appropriate response recorder for the given path."""
    return vcr.VCR(cassette_library_dir=os.path.join(os.path.dirname(test_file_path),
                                                     'fixtures'))
