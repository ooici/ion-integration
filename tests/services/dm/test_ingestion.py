#!/usr/bin/env python

"""
@file inttest_ingest.py
@author Dave Foster <dfoster@asascience.com>
@test 
"""

import ion.util.ionlog
from twisted.internet import defer

from ion.test.iontest import ItvTestCase
from ion.core import ioninit
from ion.core.exception import ReceivedApplicationError
from ion.util import procutils as pu
from ion.integration.eoi.agent.java_agent_wrapper import JavaAgentWrapperClient
from ion.services.coi.datastore_bootstrap.ion_preload_config import SAMPLE_PROFILE_DATASET_ID, SAMPLE_PROFILE_DATA_SOURCE_ID

log = ion.util.ionlog.getLogger(__name__)
CONF = ioninit.config(__name__)

class IntTestIngest(ItvTestCase):

    app_dependencies = [
                # four copies of ingest services
                ("res/apps/ingestion.app", "id=1"),
                ("res/apps/ingestion.app", "id=2"),
                ("res/apps/ingestion.app", "id=3"),
                ("res/apps/ingestion.app", "id=4"),
                # four copies of JAW
                ("res/apps/eoiagent.app", "id=1"),
                ("res/apps/eoiagent.app", "id=2"),
                ("res/apps/eoiagent.app", "id=3"),
                ("res/apps/eoiagent.app", "id=4"),
                # one resource registry with demodata registered
                ("res/apps/resources.app", "register=demodata"),
                ]

    @defer.inlineCallbacks
    def setUp(self):
        yield self._start_container()

    @defer.inlineCallbacks
    def tearDown(self):
        yield self._stop_container()

    @defer.inlineCallbacks
    def test_ingest(self):
        # get a subscriber going to notification from ingest service
        jawc = JavaAgentWrapperClient()
        resp = yield jawc.request_update(SAMPLE_PROFILE_DATASET_ID, SAMPLE_PROFILE_DATA_SOURCE_ID)

    @defer.inlineCallbacks
    def test_ingest4(self):

        # create four javaagentwrapperclients
        jawcs = [j() for j in [JavaAgentWrapperClient] * 4]

        # make update calls
        defs = [jawc.request_update(SAMPLE_PROFILE_DATASET_ID, SAMPLE_PROFILE_DATA_SOURCE_ID) for jawc in jawcs]

        dl = defer.DeferredList(defs)
        yield dl

