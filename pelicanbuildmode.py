#!/usr/bin/env python
# -*- coding: utf-8 -*- #
"""
Rather than use something like environmental variables to change between
DEVELOPMENT and PRODUCTION, pelican prefers to use different config files for
the different builds.

In this case, because there is a lot of overlap we configure everything inside
pelicanconf.py and use this module to indicate which build mode to use.

This can be imported and configured inside pelicanpublish.py before importing
pelicanconf.py.
"""
from __future__ import unicode_literals
from enum import Enum


class BuildMode(Enum):
    LOCALHOST_RELATIVE = 1
    LOCALHOST_ABSOLUTE = 2
    PUBLISH = 3


# Set the default mode here
BUILD_MODE = BuildMode.LOCALHOST_RELATIVE


def get_build_mode():
    return BUILD_MODE


def set_build_mode(new_build_mode):
    global BUILD_MODE
    BUILD_MODE = new_build_mode
