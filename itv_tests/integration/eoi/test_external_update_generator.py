#!/usr/bin/env python

"""
@file tests/integration/eoi/test_external_update_generator.py
@author David Stuebe
"""

from twisted.internet import defer
from twisted.trial import unittest
import os, os.path, tempfile

from ion.core.data.cassandra_bootstrap import CassandraSchemaProvider
from ion.core.process.process import Process
from ion.core.object import object_utils
from ion.core.messaging.message_client import MessageClient
from ion.services.dm.distribution.events import ScheduleEventSubscriber
from ion.services.dm.scheduler.scheduler_service import SchedulerServiceClient, SchedulerService
from ion.core.data import storage_configuration_utility
from ion.core.data.storage_configuration_utility import STORAGE_PROVIDER, PERSISTENT_ARCHIVE
from ion.util.os_process import OSProcess

from iontest.iontest import IonTestCase
import ion.util.ionlog
from ion.util.iontime import IonTime
from ion.util.procutils import asleep

log = ion.util.ionlog.getLogger(__name__)

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

        # we need ioncore-java-runnables
        # get around that trial_temp dir, and no don't use adjust_dir, doesn't matter here, this is always a test
        self.bin_dir = os.path.join("..", "..", "ioncore-java-runnables")

        if not os.path.exists(self.bin_dir):
            raise unittest.SkipTest("could not find ioncore-java-runnables at %s" % self.bin_dir)

        self.java = os.path.join("/usr", "bin", "java")
        if not os.path.exists(self.java):
            raise unittest.SkipTest("could not find java at %s" % self.java)

        yield self._start_container()

        self.proc = Process()
        yield self.proc.spawn()

        # setup subscriber for trigger event
        self._notices = []
        self.sub = ScheduleEventSubscriber(process=self.proc,
                                           origin=SCHEDULE_TYPE_PERFORM_INGESTION_UPDATE)

        self._def_notice_received = defer.Deferred()

        # you can not keep the received message around after the ondata callback is complete
        def datame(c):
            self._notices.append(c['content'].additional_data.payload.dataset_id)
            self._def_notice_received.callback(True)

        self.sub.ondata = datame
        #yield self.proc.register_life_cycle_object(self.sub)
        yield self.sub.initialize()
        yield self.sub.activate()


    @defer.inlineCallbacks
    def tearDown(self):

        yield self._shutdown_processes()
        yield self._stop_container()


    @defer.inlineCallbacks
    def test_external_event(self):

        # create a temporary ooici-conn.properties file
        tf = tempfile.NamedTemporaryFile()

        propstempl = '''
ion.host=%s
ion.sysname=%s
ion.event_exchange=events.topic
ion.update_event_topic=2001.1001
'''
        exp = propstempl % (ioninit.container_instance.exchange_manager.exchange_space.message_space.hostname,
                            ioninit.sys_name)

        tf.write(exp)

        osp = OSProcess(binary=self.java, spawnargs=["-cp", ".:*:lib/*", 'ion.integration.eoi.UpdateEventGenerator', 'fake-dataset-id'], startdir=self.bin_dir)

        yield osp.spawn()
        tf.close()

        yield self._def_notice_received

        self.failUnless(len(self._notices) == 1, "Did not see the message - check your sysname/env")

