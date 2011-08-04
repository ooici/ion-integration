"""
@file tests/integration/ais/test_ais.py
@author Matt Rodriguez
@brief Starts the AIS processes in different containers, makes requests of the AIS application 
tracks the memory process.

This is for performance benchmarking.
"""
import time
from twisted.internet import defer

from iontest.iontest import ItvTestCase

from ion.integration.ais.test import test_app_integration as app_integration_module

import ion.util.ionlog
log = ion.util.ionlog.getLogger(__name__)

from ion.util import procutils as pu

from ion.core.process.process import Process

from ion.core.messaging.message_client import MessageClient
from ion.integration.ais.app_integration_service import AppIntegrationServiceClient
from ion.services.coi.resource_registry.resource_client import ResourceClient
from ion.services.coi.resource_registry.association_client import AssociationClient


"""

class TestAISProcesses(ItvTestCase, app_integration_module.AppIntegrationTest):
    
    app_dependencies = ["res/apps/datastore.app",
                       "res/apps/association.app",
                       "res/apps/resource_registry.app",
                       "res/apps/ems.app",
                       "res/apps/attributestore.app",
                       "res/apps/identity_registry.app",
                       "res/apps/pubsub.app",
                       "res/apps/scheduler.app",
                       "res/apps/dataset_controller.app",
                       "res/apps/app_integration.app",
                       "res/apps/notification_alert.app"
                       ]

    
    @defer.inlineCallbacks
    def setUp(self):
        self.t = time.time()
        yield self._start_container()
        
        proc = Process()
        yield proc.spawn()
        
        self.mc = MessageClient(proc)
        self.aisc = AppIntegrationServiceClient(proc)
        self.rc = ResourceClient(proc)
        self.ac  = AssociationClient(proc)
        self._proc = proc
    
    @defer.inlineCallbacks
    def tearDown(self):
        print pu.print_memory_usage()
        yield self._stop_container()

        
    def test_instantiate(self):
        log.info("Started the containers")
        
     
"""
