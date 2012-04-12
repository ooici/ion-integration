#!/usr/bin/env python

"""
@file ion/services/coi/test/test_datastore.py
@author David Stuebe
@author David Foster
@author Matt Rodriguez
"""
import os 
import subprocess


import ion.util.ionlog
log = ion.util.ionlog.getLogger(__name__)
from twisted.internet import defer

from ion.core import ioninit
CONF = ioninit.config(__name__)

from ion.util import procutils as pu

from ion.core.data import cassandra_bootstrap
from ion.core.data import storage_configuration_utility

from ion.core.data.storage_configuration_utility import BLOB_CACHE, COMMIT_CACHE, PERSISTENT_ARCHIVE

from ion.services.coi.datastore_bootstrap.ion_preload_config import ION_DATASETS_CFG, ION_AIS_RESOURCES_CFG, PRELOAD_CFG


from telephus.cassandra.ttypes import InvalidRequestException


from ion.services.coi.test import test_datastore as datastore_test
create_large_object = datastore_test.create_large_object

import binascii
from ion.core.object import object_utils
OPAQUE_ARRAY_TYPE = object_utils.create_type_identifier(object_id=10016, version=1)




# This is a bit of a hack - to keep it from running the tests on the original DataStoreTest class as well.
class CassandraBackedDataStoreTest(datastore_test.DataStoreTest):


    repetitions = 50

    timeout = 600
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

    services.append(datastore_test.DataStoreTest.services[1])

    # This test does not work with the cassandra backend by design!
    del datastore_test.DataStoreTest.test_put_blobs

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


        yield datastore_test.DataStoreTest.setup_services(self)


    @defer.inlineCallbacks
    def tearDown(self):

        try:
            yield self.test_harness.client.system_drop_keyspace(self.keyspace)
        except InvalidRequestException, ire:
            log.info('No Keyspace to remove in teardown: ' + str(ire))


        self.test_harness.disconnect()

        yield datastore_test.DataStoreTest.tearDown(self)





    def commit_it(self, i):
        #log.debug('Calling commit_it: %d' % i)
        self.repo.root_object.owner.name = 'my name %d' % i
        self.repo.root_object.person[0].name = 'other name %d' % i

        self.repo.commit('Commit number %d' % i)

    @defer.inlineCallbacks
    def test_push_make_busy(self):

        repo = self.wb1.workbench.get_repository(self.repo_key)

        self.repo = repo

        '''
        Fancy code - not necessary
        for i in range(1000):
            d = defer.Deferred()
            d.addCallback(self.commit_it)
            #print d.callbacks
            res = reactor.callLater(0, d.callback,i)

            #print dir(res)

            yield d
            '''

        for i in range(100):
            #log.debug('Calling commit_it: %d' % i)
            self.repo.root_object.owner.name = 'my name %d' % i
            self.repo.root_object.person[0].name = 'other name %d' % i

            self.repo.commit('Commit number %d' % i)
            yield pu.asleep(0)

            

        log.info('DataStore1 Push Complex addressbook to DataStore1. Number of objects %d' % len(repo.index_hash))

        result = yield self.wb1.workbench.push_by_name('datastore',self.repo_key)

        self.assertEqual(result.MessageResponseCode, result.ResponseCodes.OK)

        log.info('DataStore1 Push Complex addressbook to DataStore1: complete')



class CassandraBackedMulitDataStoreTest(datastore_test.MulitDataStoreTest):
    """
    Testing Datastore service.
    """

    username = CONF.getValue('cassandra_username', None)
    password = CONF.getValue('cassandra_password', None)



    services = [

            {'name':'ds2','module':'ion.services.coi.datastore','class':'DataStoreService',
             'spawnargs':{COMMIT_CACHE:'ion.core.data.cassandra_bootstrap.CassandraIndexedStoreBootstrap',
                          BLOB_CACHE:'ion.core.data.cassandra_bootstrap.CassandraStoreBootstrap',PRELOAD_CFG:datastore_test.MulitDataStoreTest.preload, }
        },
            {'name':'ds3','module':'ion.services.coi.datastore','class':'DataStoreService',
             'spawnargs':{COMMIT_CACHE:'ion.core.data.cassandra_bootstrap.CassandraIndexedStoreBootstrap',
                          BLOB_CACHE:'ion.core.data.cassandra_bootstrap.CassandraStoreBootstrap',PRELOAD_CFG:datastore_test.MulitDataStoreTest.preload}
        },
            {'name':'ds4','module':'ion.services.coi.datastore','class':'DataStoreService',
             'spawnargs':{COMMIT_CACHE:'ion.core.data.cassandra_bootstrap.CassandraIndexedStoreBootstrap',
                          BLOB_CACHE:'ion.core.data.cassandra_bootstrap.CassandraStoreBootstrap',PRELOAD_CFG:datastore_test.MulitDataStoreTest.preload}
        },

        # Start this one last to preload...
            {'name':'ds1','module':'ion.services.coi.datastore','class':'DataStoreService',
             'spawnargs':{COMMIT_CACHE:'ion.core.data.cassandra_bootstrap.CassandraIndexedStoreBootstrap',
                          BLOB_CACHE:'ion.core.data.cassandra_bootstrap.CassandraStoreBootstrap'}
             }, # The first one does the preload by default

            {'name':'workbench_test1',
             'module':'ion.core.object.test.test_workbench',
             'class':'WorkBenchProcess',
             'spawnargs':{'proc-name':'wb1'}
        },

            {'name':'workbench_test2',
             'module':'ion.core.object.test.test_workbench',
             'class':'WorkBenchProcess',
             'spawnargs':{'proc-name':'wb2'}
        },
        ]


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


        yield datastore_test.MulitDataStoreTest.setup_services(self)


    @defer.inlineCallbacks
    def tearDown(self):

        try:
            yield self.test_harness.client.system_drop_keyspace(self.keyspace)
        except InvalidRequestException, ire:
            log.info('No Keyspace to remove in teardown: ' + str(ire))


        self.test_harness.disconnect()

        yield datastore_test.MulitDataStoreTest.tearDown(self)

