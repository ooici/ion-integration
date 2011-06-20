#!/usr/bin/env python

"""
@file inttest_ingest.py
@author Dave Foster <dfoster@asascience.com>
@test 
"""

import ion.util.ionlog
from twisted.internet import defer

from iontest.iontest import ItvTestCase
from ion.core import ioninit
from ion.core.exception import ReceivedApplicationError
from ion.util import procutils as pu
from ion.util.iontime import IonTime

from ion.integration.eoi.agent.java_agent_wrapper import JavaAgentWrapperClient

from ion.core.process import process
from ion.services.coi.resource_registry import resource_client
from ion.services.coi.resource_registry import association_client

from ion.core.object.object_utils import CDM_DATASET_TYPE, CDM_GROUP_TYPE, create_type_identifier

from ion.services.dm.distribution.events import DatasourceUnavailableEventSubscriber, DatasetSupplementAddedEventSubscriber, ScheduleEventPublisher

from ion.services.dm.scheduler.scheduler_service import SCHEDULE_TYPE_PERFORM_INGESTION_UPDATE

from ion.services.coi.datastore_bootstrap.ion_preload_config import HAS_A_ID

DATA_SOURCE_RESOURCE_TYPE   = create_type_identifier(object_id=4503, version=1)
THREDDS_AUTHENTICATION_TYPE = create_type_identifier(object_id=4504, version=1)
SCHEDULER_PERFORM_INGEST    = create_type_identifier(object_id=2607, version=1)



log = ion.util.ionlog.getLogger(__name__)
CONF = ioninit.config(__name__)

class IntTestIngest(ItvTestCase):

    app_dependencies = [

                ("res/deploy/bootlevel4_local.rel", "id=1"),
                #("res/deploy/bootlevel4.rel", "id=1"),
                #("res/deploy/bootlevel4.rel", "id=2","do-init=False"),
                ("res/deploy/bootlevel5.rel", "id=1"),
                ("res/apps/pubsub.app", "id=1"),
                ("res/apps/ingestion.app", "id=1"),

                ("res/apps/eoiagents.app", "id=1"),

                ]

    timeout = 120

    @defer.inlineCallbacks
    def setUp(self):
        yield self._start_container()
        self.proc = process.Process()
        yield self.proc.spawn()


        self.rc = resource_client.ResourceClient(proc=self.proc)

        self.ac = association_client.AssociationClient(proc=self.proc)

    @defer.inlineCallbacks
    def tearDown(self):
        yield self._stop_container()

    @defer.inlineCallbacks
    def test_rpc_jaw_ingest(self):

        yield self.jaw_ingest_test(self.rpc_call_jaw)


    @defer.inlineCallbacks
    def test_scheduled_jaw_ingest(self):

        yield self.jaw_ingest_test(self.scheduled_jaw_event)



    @defer.inlineCallbacks
    def jaw_ingest_test(self, call_jaw):


        dataset = yield self.rc.create_instance(CDM_DATASET_TYPE,
                                                ResourceName = 'Blank dataset for testing ingestion',
                                                ResourceDescription= 'An example of a station dataset')

        group = dataset.CreateObject(CDM_GROUP_TYPE)
        dataset.root_group = group

        #group.name = 'David'

        #log.debug(dataset.ResourceObject.PPrint())

        datasource = yield self.rc.create_instance(DATA_SOURCE_RESOURCE_TYPE,
                                                ResourceName = 'CGSN example for ingestion testing',
                                                ResourceDescription= 'An example of a data source for the CGSN OSU dataset for testing ingestion')


        datasource.source_type = datasource.SourceType.NETCDF_S
        datasource.request_type = datasource.RequestType.DAP

        datasource.dataset_url = "http://uop.whoi.edu/oceansites/ooi/OS_NTAS_2010_R_M-1.nc"

        datasource.max_ingest_millis = 120000
        
        datasource.registration_datetime_millis = IonTime().time_ms

        datasource.ion_title = "NTAS 1"
        datasource.ion_description = "OSU CGSN"

        datasource.update_interval_seconds = 86400

        datasource.aggregation_rule = datasource.AggregationRule.OVERLAP

        #datasource.authentication = datasource.CreateObject(THREDDS_AUTHENTICATION_TYPE)
        #datasource.authentication.name = 'cgsn'
        #datasource.authentication.password = "ISMT2!!"


        # Just create it - the workbench/datastore will take care of the rest!
        asssociation = yield self.ac.create_association(datasource, HAS_A_ID,  dataset)

        yield self.rc.put_resource_transaction([dataset, datasource])


        #log.debug(dataset.ResourceObject.Debug())

        log.info('Created dataset and datasource for testing')


        sub_added = DatasetSupplementAddedEventSubscriber(process=self.proc, origin=dataset.ResourceIdentity)
        yield sub_added.initialize()
        yield sub_added.activate()

        sub_added.ondata = lambda msg: test_deferred.callback( msg['content'].additional_data.datasource_id)

        test_deferred = defer.Deferred()

        log.info('Created subscriber to listen for test results')

        yield call_jaw(dataset.ResourceIdentity, datasource.ResourceIdentity)



        datasource_id = yield test_deferred

        self.assertEqual(datasource_id, datasource.ResourceIdentity)


    @defer.inlineCallbacks
    def rpc_call_jaw(self, dataset_id, datasource_id):

        # get a subscriber going to notification from ingest service
        jawc = JavaAgentWrapperClient()
        resp = yield jawc.request_update(dataset_id, datasource_id)


    @defer.inlineCallbacks
    def scheduled_jaw_event(self, dataset_id, datasource_id):

        pub = ScheduleEventPublisher(process=self.proc)

        msg = yield pub.create_event(origin=SCHEDULE_TYPE_PERFORM_INGESTION_UPDATE,
                                          task_id="manage_data_resource_FAKED_TASK_ID")

        msg.additional_data.payload = msg.CreateObject(SCHEDULER_PERFORM_INGEST)
        msg.additional_data.payload.dataset_id     = dataset_id
        msg.additional_data.payload.datasource_id  = datasource_id


        yield pub.publish_event(msg, origin=SCHEDULE_TYPE_PERFORM_INGESTION_UPDATE)




    """
    @defer.inlineCallbacks
    def test_ingest4(self):

        # create four javaagentwrapperclients
        jawcs = [j() for j in [JavaAgentWrapperClient] * 4]

        # make update calls
        defs = [jawc.request_update(SAMPLE_PROFILE_DATASET_ID, SAMPLE_PROFILE_DATA_SOURCE_ID) for jawc in jawcs]

        dl = defer.DeferredList(defs)
        yield dl

    """
