#!/usr/bin/env python

"""
@file ion/services/coi/test/test_datastore.py
@author David Stuebe
@author David Foster
@author Matt Rodriguez
"""

import ion.util.ionlog
log = ion.util.ionlog.getLogger(__name__)
from twisted.internet import defer

from ion.core import ioninit
CONF = ioninit.config(__name__)


from ion.core.data import cassandra_bootstrap
from ion.core.data import storage_configuration_utility

from ion.core.data.storage_configuration_utility import BLOB_CACHE, COMMIT_CACHE, PERSISTENT_ARCHIVE

from ion.services.coi.datastore_bootstrap.ion_preload_config import ION_DATASETS_CFG, ION_AIS_RESOURCES_CFG, PRELOAD_CFG


from telephus.cassandra.ttypes import InvalidRequestException


from ion.services.coi.test import test_datastore as import_test_datastore


class CassandraBackedDataStoreTest(import_test_datastore.DataStoreTest):


    username = CONF.getValue('cassandra_username', None)
    password = CONF.getValue('cassandra_password', None)

    services=[]
    services.append(
        {'name':'ds1','module':'ion.services.coi.datastore','class':'DataStoreService',
         'spawnargs':{COMMIT_CACHE:'ion.core.data.cassandra_bootstrap.CassandraIndexedStoreBootstrap',
                      BLOB_CACHE:'ion.core.data.cassandra_bootstrap.CassandraStoreBootstrap',
                      PRELOAD_CFG:{ION_DATASETS_CFG:True, ION_AIS_RESOURCES_CFG:True},
                      "username": username,
                      "password": password }
                })

    services.append(import_test_datastore.DataStoreTest.services[1])


    @defer.inlineCallbacks
    def setUp(self):

        yield self._start_container()

        storage_conf = storage_configuration_utility.get_cassandra_configuration()

        self.keyspace = storage_conf[PERSISTENT_ARCHIVE]["name"]

        # Use a test harness cassandra client to set it up the way we want it for the test and tear it down
        test_harness = cassandra_bootstrap.CassandraSchemaProvider(self.username, self.password, storage_conf, error_if_existing=False)

        test_harness.connect()

        self.test_harness = test_harness


        try:
            yield self.test_harness.client.system_drop_keyspace(self.keyspace)
        except InvalidRequestException, ire:
            log.info('No Keyspace to remove in setup: ' + str(ire))

        yield test_harness.run_cassandra_config()


        yield import_test_datastore.DataStoreTest.setup_services(self)


    @defer.inlineCallbacks
    def tearDown(self):

        try:
            yield self.test_harness.client.system_drop_keyspace(self.keyspace)
        except InvalidRequestException, ire:
            log.info('No Keyspace to remove in teardown: ' + str(ire))


        self.test_harness.disconnect()

        yield import_test_datastore.DataStoreTest.tearDown(self)


    # This test does not work with the cassandra backend by design!
    del import_test_datastore.DataStoreTest.test_put_blobs
