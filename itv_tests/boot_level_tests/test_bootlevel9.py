#!/usr/bin/env python

"""
@file test_bootlevel89.py
@test Bootlevel 9 ready checks.
"""

import ion.util.ionlog
from twisted.internet import defer
from iontest.iontest import ItvTestCase
from ion.core import ioninit
from ion.core.process.process import Process

log = ion.util.ionlog.getLogger(__name__)
CONF = ioninit.config(__name__)

class Bootlevel9ReadyTest(ItvTestCase):

    app_dependencies = ["res/deploy/bootlevel4_local.rel",
                        "res/deploy/bootlevel5.rel",
                        "res/deploy/bootlevel6.rel",
                        "res/deploy/bootlevel7.rel",
                        "res/deploy/bootlevel8.rel",
                        "res/deploy/bootlevel9.rel",
                        ]
    @defer.inlineCallbacks
    def setUp(self):
        yield self._start_container()

    @defer.inlineCallbacks
    def tearDown(self):
        yield self._stop_container()

    @defer.inlineCallbacks
    def test_all_services(self):
        p = Process()
        yield p.spawn()

        for servicename in ['ingestion','notification_alert','store_service','cdm_validation_service','app_integration']:
            (content, headers, msg) = yield p.rpc_send(p.get_scoped_name('system', servicename), 'ping', {})
            # if timeout, will just fail the test

