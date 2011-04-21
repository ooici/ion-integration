#!/usr/bin/env python

"""
@file sample_integration_test.py
@author David Stuebe
@test Example test file
"""

import ion.util.ionlog
from twisted.internet import defer
from ion.test.iontest import ItvTestCase
from ion.core import ioninit
from ion.core.process.process import Process

from ion.core.process.test.test_service import EchoServiceTest

log = ion.util.ionlog.getLogger(__name__)
CONF = ioninit.config(__name__)

class SampleTest(ItvTestCase, EchoServiceTest):

    app_dependencies = ["res/apps/echo_example.app"]

    services=[]

    @defer.inlineCallbacks
    def setUp(self):
        yield self._start_container()

    @defer.inlineCallbacks
    def tearDown(self):
        yield self._stop_container()

    @defer.inlineCallbacks
    def test_something(self):
        p = Process()
        yield p.spawn()



