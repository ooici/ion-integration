#!/usr/bin/env python

"""
@file inttest_ingest.py
@author Ian Katz <ijk5@mit.edu>
@test
"""

import ion.util.ionlog
from twisted.internet import defer

from ion.test.iontest import ItvTestCase
from ion.core import ioninit
from ion.core.exception import ReceivedApplicationError
from ion.util import procutils as pu

from ion.integration.ais.app_integration_service import AppIntegrationServiceClient
from ion.services.coi.resource_registry_beta.resource_client import ResourceClient
from ion.core.messaging.message_client import MessageClient
from ion.core.process.process import Process

from ion.integration.ais.ais_object_identifiers import AIS_RESPONSE_MSG_TYPE, \
                                                       AIS_REQUEST_MSG_TYPE, \
                                                       AIS_RESPONSE_ERROR_TYPE, \
                                                       CREATE_DATA_RESOURCE_REQ_TYPE, \
                                                       CREATE_DATA_RESOURCE_RSP_TYPE, \
                                                       UPDATE_DATA_RESOURCE_REQ_TYPE, \
                                                       UPDATE_DATA_RESOURCE_RSP_TYPE, \
                                                       DELETE_DATA_RESOURCE_REQ_TYPE, \
                                                       DELETE_DATA_RESOURCE_RSP_TYPE


from ion.services.coi.datastore_bootstrap.ion_preload_config import SAMPLE_PROFILE_DATASET_ID, SAMPLE_PROFILE_DATA_SOURCE_ID

log = ion.util.ionlog.getLogger(__name__)
CONF = ioninit.config(__name__)

class IntTestAIS(ItvTestCase):

    app_dependencies = [
                # release file for r1
                ("res/deploy/r1deploy.rel", "id=1"),
                ]

    @defer.inlineCallbacks
    def setUp(self):
        yield self._start_container()

        proc  = Process()
        yield proc.spawn()

        self.aisc  = AppIntegrationServiceClient(proc=proc)
        self.rc    = ResourceClient(proc=proc)
        self.mc    = MessageClient(proc=proc)


    @defer.inlineCallbacks
    def tearDown(self):
        yield self._stop_container()


    @defer.inlineCallbacks
    def test_createDataResource(self):
        yield self._createDataResource()

    @defer.inlineCallbacks
    def _createDataResource(self):
        
        ais_req_msg     = yield self.mc.create_instance(AIS_REQUEST_MSG_TYPE)
        self.failIfEqual(type(ais_req_msg), type(0), "ais_req_msg is weird")


        #use the wrong type of GPB
        result = yield self.aisc.createDataResource(ais_req_msg)

        self.failUnlessEqual(result.MessageType, AIS_RESPONSE_ERROR_TYPE, 
                             "createDataResource accepted a GPB that was known to be the wrong type")
            

        create_req_msg  = yield self.mc.create_instance(CREATE_DATA_RESOURCE_REQ_TYPE)

        #test empty (fields missing) GPB
        yield self._checkFieldAcceptance(create_req_msg)

        #test full field set but no URLs
        create_req_msg.user_id                       = "A3D5D4A0-7265-4EF2-B0AD-3CE2DC7252D8"
        create_req_msg.source_type                   = create_req_msg.SourceType.NETCDF_S
        create_req_msg.request_type                  = create_req_msg.RequestType.DAP
        create_req_msg.ion_description               = "FIXME: description"
        create_req_msg.ion_institution_id            = "FIXME: institution_id"
        create_req_msg.update_start_datetime_millis  = 30000
        create_req_msg.ion_title                     = "some lame title"
        create_req_msg.update_interval_seconds       = 3600
        yield self._checkFieldAcceptance(create_req_msg)

        #test too many URLs
        create_req_msg.base_url     = "FIXME"
        create_req_msg.dataset_url  = "http://thredds1.pfeg.noaa.gov/thredds/dodsC/satellite/GR/ssta/1day"
        yield self._checkFieldAcceptance(create_req_msg)

        create_req_msg.ClearField("base_url")


        #should be ready for actual action
        result = yield self.aisc.createDataResource(req_msg)

        self.failUnlessEqual(result.MessageType, AIS_RESPONSE_MSG_TYPE)

        #fixme: look up resource from returned id
        #fixme: check that fields match what we put in
        #fixme: check the association
        
        defer.returnValue(result)

                             

    @defer.inlineCallbacks
    def _checkFieldAcceptance(self, req_msg):
        
        result = yield self.aisc.createDataResource(req_msg)
        self.failUnlessEqual(result.MessageType, AIS_RESPONSE_ERROR_TYPE, 
                             "createDataResource accepted a GPB that was known to be lacking data")
        
        defer.returnValue(None)
        
        
        
