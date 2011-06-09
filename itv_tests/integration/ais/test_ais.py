"""
@file tests/integration/ais/test_ais.py
@author Matt Rodriguez
@brief Starts the AIS processes in different containers, makes requests of the AIS application 
tracks the memory process.
"""
import time
import ion.util.ionlog
from twisted.internet import defer

from iontest.iontest import ItvTestCase

from ion.core import ioninit


from ion.integration.ais.test import test_app_integration as app_integration_module

import ion.util.ionlog
log = ion.util.ionlog.getLogger(__name__)

from ion.core.process.process import Process

from ion.core.messaging.message_client import MessageClient
from ion.integration.ais.app_integration_service import AppIntegrationServiceClient
from ion.services.coi.resource_registry.resource_client import ResourceClient

from ion.integration.ais.ais_object_identifiers import AIS_REQUEST_MSG_TYPE, AIS_RESPONSE_ERROR_TYPE

from ion.integration.ais.ais_object_identifiers import FIND_DATA_RESOURCES_REQ_MSG_TYPE

from ion.services.coi.datastore_bootstrap.ion_preload_config import ANONYMOUS_USER_ID


class TestAISProcesses(ItvTestCase, app_integration_module.AppIntegrationTest):
    timeout = 77

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
        self._proc = proc
    
    @defer.inlineCallbacks
    def tearDown(self):
        self._print_memory_usage()
        yield self._stop_container()

        
    def test_instantiate(self):
        log.info("Started the containers")
        
     
        
    @defer.inlineCallbacks
    def test_memory_footprint(self):
        """
        Test for the return of notificationSet field: this is in a separate test
        to make it convenient for unit testing.  The notificationSet field is
        actually returned in the findDataResources response, but it will only
        be set if there is a subscription set for a dataset/userID combo, which
        this test scenario sets up.
        """

        log.debug('Testing findDataResources.')

        #
        # Send a message with no bounds
        #
        
        # Create a message client
        
        # create a request message 
        reqMsg = yield self.mc.create_instance(AIS_REQUEST_MSG_TYPE)
        reqMsg.message_parameters_reference = reqMsg.CreateObject(FIND_DATA_RESOURCES_REQ_MSG_TYPE)

        reqMsg.message_parameters_reference.user_ooi_id  = ANONYMOUS_USER_ID
        print "Calling find data resources"
        d = self.aisc.findDataResources(reqMsg)
        
        yield d
        log.info("findDataResources complete")
        rspMsg = d.result
        if rspMsg.MessageType == AIS_RESPONSE_ERROR_TYPE:
            self.fail("findDataResources failed: " + rspMsg.error_str)

        numResReturned = len(rspMsg.message_parameters_reference[0].dataResourceSummary)
        log.info('findDataResources returned: ' + str(numResReturned) + ' resources.')
        
