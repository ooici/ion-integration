#!/usr/bin/env python

"""
@file inttest_bootlevel4_local.py
@author Dave Foster <dfoster@asascience.com>
@test Bootlevel 4 ready checks (local services only).
"""

from ion.test.iontest import ItvTestCase

class DoesNothing(ItvTestCase):

    app_dependencies = []

    def test_nada(self):
        pass

