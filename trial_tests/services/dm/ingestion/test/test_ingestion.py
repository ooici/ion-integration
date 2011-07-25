#!/usr/bin/env python

"""
@file trial_tests/services/dm/ingestion/test/test_ingestion.py
@author David Stuebe
@author Matt Rodriguez
@brief test for eoi ingestion demo
"""

import ion.util.ionlog
log = ion.util.ionlog.getLogger(__name__)
from twisted.internet import defer, reactor

from ion.util.iontime import IonTime
from ion.core import ioninit
from ion.services.coi.datastore_bootstrap.ion_preload_config import PRELOAD_CFG, ION_DATASETS_CFG, SAMPLE_PROFILE_DATASET_ID, TYPE_CFG, NAME_CFG, DESCRIPTION_CFG, CONTENT_CFG, ID_CFG


from ion.core.process import process
from ion.services.dm.ingestion.ingestion import IngestionClient, SUPPLEMENT_MSG_TYPE, CDM_DATASET_TYPE, DAQ_COMPLETE_MSG_TYPE, PERFORM_INGEST_MSG_TYPE
from ion.test.iontest import IonTestCase
from ion.services.coi.datastore_bootstrap.dataset_bootstrap import BOUNDED_ARRAY_TYPE, FLOAT32ARRAY_TYPE, bootstrap_byte_array_dataset


from ion.core.object.object_utils import create_type_identifier


DATASET_TYPE = create_type_identifier(object_id=10001, version=1)
DATASOURCE_TYPE = create_type_identifier(object_id=4503, version=1)
GROUP_TYPE = create_type_identifier(object_id=10020, version=1)


CONF = ioninit.config(__name__)


def create_delayed_call(timeoutval=None):
    timeoutval = timeoutval or 10000
    def _timeout():
        # do nothing
        pass
    dc = reactor.callLater(timeoutval, _timeout)
    dc.ingest_service_timeout = timeoutval
    return dc

class IngestionTest(IonTestCase):
    """
    Testing service operations of the ingestion service.
    """

    @defer.inlineCallbacks
    def setUp(self):
        yield self._start_container()
        services = [
            {   'name':'ds1',
                'module':'ion.services.coi.datastore',
                'class':'DataStoreService',
                'spawnargs':
                        {PRELOAD_CFG:
                                 {ION_DATASETS_CFG:True}
                        }
            },

            {
                'name':'resource_registry1',
                'module':'ion.services.coi.resource_registry.resource_registry',
                'class':'ResourceRegistryService',
                    'spawnargs':{'datastore_service':'datastore'}
            },

            {
                'name':'exchange_management',
                'module':'ion.services.coi.exchange.exchange_management',
                'class':'ExchangeManagementService',
            },

            {
                'name':'association_service',
                'module':'ion.services.dm.inventory.association_service',
                'class':'AssociationService'
            },
            {
                'name':'pubsub_service',
                'module':'ion.services.dm.distribution.pubsub_service',
                'class':'PubSubService'
            },

            {   'name':'ingestion1',
                'module':'ion.services.dm.ingestion.ingestion',
                'class':'IngestionService'
            },

            ]

        # ADD PUBSUB AND EMS

        self.sup = yield self._spawn_processes(services)

        self.proc = process.Process()
        yield self.proc.spawn()

        self._ic = IngestionClient(proc=self.proc)

        ingestion1 = yield self.sup.get_child_id('ingestion1')
        log.debug('Process ID:' + str(ingestion1))
        self.ingest= self._get_procinstance(ingestion1)
        
        self.ingest.timeoutcb = create_delayed_call()
        
        ds1 = yield self.sup.get_child_id('ds1')
        log.debug('Process ID:' + str(ds1))
        self.datastore= self._get_procinstance(ds1)


    class fake_msg(object):

        def ack(self):
            return True


    @defer.inlineCallbacks
    def tearDown(self):
        # You must explicitly clear the registry in case cassandra is used as a back end!
        yield self._stop_container()


    @defer.inlineCallbacks
    def create_and_test_variable_chunk(self, var_name):

        group = self.ingest.dataset.root_group
        var = group.FindVariableByName(var_name)
        starting_bounded_arrays  = var.content.bounded_arrays[:]

        supplement_msg = yield self.ingest.mc.create_instance(SUPPLEMENT_MSG_TYPE)
        supplement_msg.dataset_id = SAMPLE_PROFILE_DATASET_ID
        supplement_msg.variable_name = var_name

        self.create_chunk(supplement_msg)

        # Call the op of the ingest process directly
        yield self.ingest.op_recv_chunk(supplement_msg, '', self.fake_msg())

        updated_bounded_arrays = var.content.bounded_arrays[:]

        # This is all we really need to do - make sure that the bounded array has been added.
        self.assertEqual(len(updated_bounded_arrays), len(starting_bounded_arrays)+1)

        # The bounded array but not the ndarray should be in the ingestion service dataset
        self.assertIn(supplement_msg.bounded_array.MyId, self.ingest.dataset.Repository.index_hash)
        self.assertNotIn(supplement_msg.bounded_array.ndarray.MyId, self.ingest.dataset.Repository.index_hash)

        # The datastore should now have this ndarray
        self.failUnless(self.datastore.b_store.has_key(supplement_msg.bounded_array.ndarray.MyId))


    def create_chunk(self, supplement_msg):
        """
        This method is specialized to create bounded arrays for the Sample profile dataset.
        """



        supplement_msg.bounded_array = supplement_msg.CreateObject(BOUNDED_ARRAY_TYPE)
        supplement_msg.bounded_array.ndarray = supplement_msg.CreateObject(FLOAT32ARRAY_TYPE)

        if supplement_msg.variable_name == 'time':

            tsteps = 3
            tstart = 1280106120
            delt = 3600
            supplement_msg.bounded_array.ndarray.value.extend([tstart + delt*n for n in range(tsteps)])

            supplement_msg.bounded_array.bounds.add()
            supplement_msg.bounded_array.bounds[0].origin = 0
            supplement_msg.bounded_array.bounds[0].size = tsteps

        elif supplement_msg.variable_name == 'depth':
            supplement_msg.bounded_array.ndarray.value.extend([0.0, 0.1, 0.2])
            supplement_msg.bounded_array.bounds.add()
            supplement_msg.bounded_array.bounds[0].origin = 0
            supplement_msg.bounded_array.bounds[0].size = 3

        elif supplement_msg.variable_name == 'salinity':
            supplement_msg.bounded_array.ndarray.value.extend([29.84, 29.76, 29.87, 30.16, 30.55, 30.87])
            supplement_msg.bounded_array.bounds.add()
            supplement_msg.bounded_array.bounds[0].origin = 0
            supplement_msg.bounded_array.bounds[0].size = 2
            supplement_msg.bounded_array.bounds.add()
            supplement_msg.bounded_array.bounds[1].origin = 0
            supplement_msg.bounded_array.bounds[1].size = 3


        supplement_msg.Repository.commit('Commit before fake send...')


    @defer.inlineCallbacks
    def test_ingest_from_files(self):
        """
        This is a test method for ingesting multiple updates from a set of files - simulating what the JAW/DAC do...

        'ion.services.dm.ingestion.test.test_ingestion':{
        # Path to files relative to ioncore-python directory!
        'ingest_files' :
            [
                '../../ion_data/NTAS_10_Real-time_Mooring_Data_System_1.ooicdm.tgz',
                '../../ion_data/NTAS_10_Real-time_Mooring_Data_System_1_u1.ooicdm.tgz',
                '../../ion_data/NTAS_10_Real-time_Mooring_Data_System_1_u2.ooicdm.tgz'
            ],
        },
        """

        flist = CONF.getValue('ingest_files', [])
        if not flist:
            raise RuntimeError('Expected config file entry not found: ingest_files is missing or empty!')

        new_dataset_id = 'C37A2796-E44C-47BF-BBFB-637339CE81D0'

        def create_dataset(dataset, *args, **kwargs):
            """
            Create an empty dataset
            """
            group = dataset.CreateObject(GROUP_TYPE)
            dataset.root_group = group
            return True


        
        data_set_description = {ID_CFG:new_dataset_id,
                      TYPE_CFG:DATASET_TYPE,
                      NAME_CFG:'Blank dataset for testing ingestion',
                      DESCRIPTION_CFG:'An example of a station dataset',
                      CONTENT_CFG:create_dataset,
                      }

        self.datastore._create_resource(data_set_description)
        log.info('Created Dataset Resource for test.')
         
        ds_res = self.datastore.workbench.get_repository(new_dataset_id)


        yield self.datastore.workbench.flush_repo_to_backend(ds_res)

        new_datasource_id = '0B1B4D49-6C64-452F-989A-2CDB02561BBE'
        # ============================================
        # Don't need a real data source at this time!
        # ============================================
        def create_datasource(datasource, *args, **kwargs):
            """
            Create an empty dataset
            """
            datasource.source_type = datasource.SourceType.NETCDF_S
            datasource.request_type = datasource.RequestType.DAP

            datasource.base_url = "http://not_a_real_url.edu"

            datasource.max_ingest_millis = 6000

            datasource.registration_datetime_millis = IonTime().time_ms

            datasource.ion_title = "NTAS1 Data Source"
            datasource.ion_description = "Data NTAS1"

            datasource.aggregation_rule = datasource.AggregationRule.OVERLAP

            return True

        data_source_description = {ID_CFG:new_datasource_id,
                      TYPE_CFG:DATASOURCE_TYPE,
                      NAME_CFG:'datasource for testing ingestion',
                      DESCRIPTION_CFG:'An example of a station datasource',
                      CONTENT_CFG:create_datasource,
                      }

        self.datastore._create_resource(data_source_description)

        # Receive a dataset to get setup...
        content = yield self.ingest.mc.create_instance(PERFORM_INGEST_MSG_TYPE)
        content.dataset_id = new_dataset_id
        content.datasource_id = new_datasource_id
        dsource_res = self.datastore.workbench.get_repository(new_datasource_id)
        log.info('Created Datasource Resource for test.')

        #yield self.datastore.workbench.flush_repo_to_backend(dset_res)
        yield self.datastore.workbench.flush_repo_to_backend(dsource_res)

        log.info('Data resources flushed to backend')
        # Now fake the receipt of the dataset message

        @defer.inlineCallbacks
        def do_file_update(file):
            
            log.info("Calling _prepare_ingest")
            yield self.ingest._prepare_ingest(content)
            log.info("Callying create_instance")
            cdm_dset_msg = yield self.ingest.mc.create_instance(CDM_DATASET_TYPE)
            yield bootstrap_byte_array_dataset(cdm_dset_msg, self, filename=file)

            log.info('Calling Receive Dataset')

            # Call the op of the ingest process directly
            yield self.ingest._ingest_op_recv_dataset(cdm_dset_msg, '', self.fake_msg())

            log.info('Calling Receive Dataset: Complete')

            complete_msg = yield self.ingest.mc.create_instance(DAQ_COMPLETE_MSG_TYPE)

            log.info('Calling Receive Done')

            complete_msg.status = complete_msg.StatusCode.OK
            yield self.ingest._ingest_op_recv_done(complete_msg, '', self.fake_msg())

            yield self.ingest.rc.put_instance(self.ingest.dataset)

            log.info('Calling Receive Done: Complete!')


            self.ingest._defer_ingest = defer.Deferred()

            self.ingest.dataset = None


        for file in flist:
            log.info('Loading data file to ingest: %s' % file)
            yield do_file_update(file)





