#!/usr/bin/env python

"""
@file tests/integration/eoi/test_external_update_generator.py
@author David Stuebe
"""

from twisted.internet import defer

from ion.core.data.cassandra_bootstrap import CassandraSchemaProvider, IndexType
from ion.core.process.process import Process
from ion.core.object import object_utils
from ion.core.messaging.message_client import MessageClient
from ion.services.dm.distribution.events import ScheduleEventSubscriber
from ion.services.dm.scheduler.scheduler_service import SchedulerServiceClient, SchedulerService
from ion.core.data import storage_configuration_utility
from ion.core.data.storage_configuration_utility import STORAGE_PROVIDER, PERSISTENT_ARCHIVE

from iontest.iontest import IonTestCase
import ion.util.ionlog
from ion.util.iontime import IonTime
from ion.util.procutils import asleep

log = ion.util.ionlog.getLogger(__name__)

from ion.util.itv_decorator import itv

# get configuration
from ion.core import ioninit
CONF = ioninit.config(__name__)


# other messages used for payloads
SCHEDULE_TYPE_PERFORM_INGESTION_UPDATE_PAYLOAD_TYPE = object_utils.create_type_identifier(object_id=2607, version=1)

# desired_origins
from ion.services.dm.scheduler.scheduler_service import SCHEDULE_TYPE_PERFORM_INGESTION_UPDATE


class ExternalUpdateTest(IonTestCase):


    @defer.inlineCallbacks
    def setUp(self):
        self.timeout = 10


        yield self._start_container()

        self.proc = Process()
        yield self.proc.spawn()

        # setup subscriber for trigger event
        self._notices = []
        self.sub = ScheduleEventSubscriber(process=self.proc,
                                           origin=SCHEDULE_TYPE_PERFORM_INGESTION_UPDATE)

        # you can not keep the received message around after the ondata callback is complete
        self.sub.ondata = lambda c: self._notices.append(c['content'].additional_data.payload.dataset_id)

        # normally we'd register before initialize/activate but let's not bring the PSC/EMS into the mix
        # if we can avoid it.
        yield self.sub.initialize()
        yield self.sub.activate()

    def _get_spawn_args(self):
        """
        Override this in derived tests for Cassandra setup for services, etc.
        """
        return {}

    @defer.inlineCallbacks
    def tearDown(self):

        yield self._shutdown_processes()
        yield self._stop_container()


    @defer.inlineCallbacks
    def test_external_event(self):
        # Create clients


        # @TODO use twisted process spawn to run the java update event generator.


        yield asleep(3)
        #cc = yield self.client.get_count()
        #self.failUnless(int(cc['value']) >= 1)
        self.failUnless(len(self._notices) == 1, "this may fail intermittently due to messaging")
