"""
Created on Jun 8, 2011
@file trial_tests/services/dm/inventory/test/test_association_service.py
@author David Stuebe
@author Matt Rodriguez

"""

import ion.util.ionlog
log = ion.util.ionlog.getLogger(__name__)
from twisted.internet import defer

from ion.core import ioninit
CONF = ioninit.config(__name__)


from ion.services.dm.inventory.test.test_association_service import AssociationServiceTest

from ion.core.object import object_utils

from ion.core.data import storage_configuration_utility
from ion.core.data.cassandra_bootstrap import PERSISTENT_ARCHIVE, CassandraSchemaProvider

from telephus.cassandra.ttypes import InvalidRequestException


from ion.core.data.storage_configuration_utility import BLOB_CACHE, COMMIT_CACHE

from ion.services.coi.datastore import ION_DATASETS_CFG, PRELOAD_CFG
# Pick three to test existence


from ion.services.coi.datastore_bootstrap.ion_preload_config import ION_AIS_RESOURCES_CFG


ASSOCIATION_TYPE = object_utils.create_type_identifier(object_id=13, version=1)
PREDICATE_REFERENCE_TYPE = object_utils.create_type_identifier(object_id=25, version=1)
LCS_REFERENCE_TYPE = object_utils.create_type_identifier(object_id=26, version=1)

class CassandraBackedAssociationServiceTest(AssociationServiceTest):

    username = CONF.getValue('cassandra_username', None)
    password = CONF.getValue('cassandra_password', None)



    services = [
            {'name':'ds1',
             'module':'ion.services.coi.datastore',
             'class':'DataStoreService',
             'spawnargs':{COMMIT_CACHE:'ion.core.data.cassandra_bootstrap.CassandraIndexedStoreBootstrap',
                      BLOB_CACHE:'ion.core.data.cassandra_bootstrap.CassandraStoreBootstrap',
                      PRELOAD_CFG:{ION_DATASETS_CFG:True, ION_AIS_RESOURCES_CFG:True},
                      "username": username,
                      "password": password}
            },
            {'name':'association_service',
             'module':'ion.services.dm.inventory.association_service',
             'class':'AssociationService',
             'spawnargs':{'index_store_class': 'ion.core.data.cassandra_bootstrap.CassandraIndexedStoreBootstrap',
                         "username": username,
                         "password": password}
                }
    ]

    

    @defer.inlineCallbacks
    def setUp(self):
        yield self._start_container()


        storage_conf = storage_configuration_utility.get_cassandra_configuration()

        self.keyspace = storage_conf[PERSISTENT_ARCHIVE]["name"]

        # Use a test harness cassandra client to set it up the way we want it for the test and tear it down
        test_harness = CassandraSchemaProvider(self.username, self.password, storage_conf, error_if_existing=False)

        test_harness.connect()

        self.test_harness = test_harness


        try:
            yield self.test_harness.client.system_drop_keyspace(self.keyspace)
        except InvalidRequestException, ire:
            log.info('No Keyspace to remove in setup: ' + str(ire))

        yield test_harness.run_cassandra_config()




        yield self.setup_services()


    @defer.inlineCallbacks
    def tearDown(self):

        try:
            yield self.test_harness.client.system_drop_keyspace(self.keyspace)
        except InvalidRequestException, ire:
            log.info('No Keyspace to remove in teardown: ' + str(ire))


        self.test_harness.disconnect()

        yield AssociationServiceTest.tearDown(self)