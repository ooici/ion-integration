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
from ion.util.iontime import IonTime

from ion.integration.eoi.agent.java_agent_wrapper import JavaAgentWrapperClient

from ion.core.process import process
from ion.services.coi.resource_registry import resource_client
from ion.services.coi.resource_registry import association_client

from ion.core.object.object_utils import CDM_DATASET_TYPE, CDM_GROUP_TYPE, create_type_identifier

from ion.services.coi.datastore_bootstrap.ion_preload_config import HAS_A_ID

DATA_SOURCE_RESOURCE_TYPE = create_type_identifier(object_id=4503, version=1)


log = ion.util.ionlog.getLogger(__name__)
CONF = ioninit.config(__name__)

class IntTestIngest(ItvTestCase):

    app_dependencies = [
                # four copies of ingest services
                #("res/deploy/ingestion.rel", "id=1"),
                ("res/deploy/r1deploy.rel", "id=1"),

                ("res/apps/eoiagent.app", "id=1"),
                #("res/apps/eoiagent.app", "id=2"),
                #("res/apps/eoiagent.app", "id=3"),
                #("res/apps/eoiagent.app", "id=4"),

                ]

    timeout = 60

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
    def test_ingest(self):


        dataset = yield self.rc.create_instance(CDM_DATASET_TYPE,
                                                ResourceName = 'Blank dataset for testing ingestion',
                                                ResourceDescription= 'An example of a station dataset')

        group = dataset.CreateObject(CDM_GROUP_TYPE)
        dataset.root_group = group



        datasource = yield self.rc.create_instance(DATA_SOURCE_RESOURCE_TYPE,
                                                ResourceName = 'NTAS RT for ingestion testing',
                                                ResourceDescription= 'An example of a data source for the NTAS RT dataset for testing ingestion')


        # Just create it - the workbench/datastore will take care of the rest!
        asssociation = yield self.ac.create_association(datasource, HAS_A_ID,  dataset)

        datasource.source_type = datasource.SourceType.NETCDF_S
        datasource.request_type = datasource.RequestType.DAP

        datasource.base_url = "http://geoport.whoi.edu/thredds/dodsC/usgs/data0/rsignell/data/oceansites/OS_NTAS_2010_R_M-1.nc"

        datasource.max_ingest_millis = 6000
        
        datasource.registration_datetime_millis = IonTime().time_ms

        datasource.ion_title = "NTAS1 Data Source"
        datasource.ion_description = "Data NTAS1"

        yield self.rc.put_resource_transaction([dataset, datasource])

        print datasource

        print dataset


        # get a subscriber going to notification from ingest service
        jawc = JavaAgentWrapperClient()
        resp = yield jawc.request_update(dataset.ResourceIdentity, datasource.ResourceIdentity)

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