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
from twisted.internet import defer, reactor

from ion.core import ioninit
CONF = ioninit.config(__name__)


from ion.core.data import cassandra_bootstrap
from ion.core.data import storage_configuration_utility

from ion.core.data.storage_configuration_utility import BLOB_CACHE, COMMIT_CACHE, PERSISTENT_ARCHIVE

from ion.services.coi.datastore_bootstrap.ion_preload_config import ION_DATASETS_CFG, ION_AIS_RESOURCES_CFG, PRELOAD_CFG


from telephus.cassandra.ttypes import InvalidRequestException


from ion.services.coi.test.test_datastore import DataStoreTest

from ion.core.object import object_utils
OPAQUE_ARRAY_TYPE = object_utils.create_type_identifier(object_id=10016, version=1)


class CassandraBackedDataStoreTest(DataStoreTest):


    timeout = 300
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

    services.append(DataStoreTest.services[1])


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


        yield DataStoreTest.setup_services(self)


    @defer.inlineCallbacks
    def tearDown(self):

        try:
            yield self.test_harness.client.system_drop_keyspace(self.keyspace)
        except InvalidRequestException, ire:
            log.info('No Keyspace to remove in teardown: ' + str(ire))


        self.test_harness.disconnect()

        yield DataStoreTest.tearDown(self)


    # This test does not work with the cassandra backend by design!
    del DataStoreTest.test_put_blobs


    def commit_it(self, i):
        #log.debug('Calling commit_it: %d' % i)
        self.repo.root_object.owner.name = 'my name %d' % i
        self.repo.root_object.person[0].name = 'other name %d' % i

        self.repo.commit('Commit number %d' % i)

    """
    These tests need to be moved into the itv_tests directory
    @defer.inlineCallbacks
    def test_push_make_busy(self):

        repo = self.wb1.workbench.get_repository(self.repo_key)

        self.repo = repo


        for i in range(1000):
            d = defer.Deferred()
            d.addCallback(self.commit_it)
            #print d.callbacks
            res = reactor.callLater(0, d.callback,i)

            #print dir(res)

            yield d


        log.info('DataStore1 Push Complex addressbook to DataStore1. Number of objects %d' % len(repo.index_hash))

        result = yield self.wb1.workbench.push_by_name('datastore',self.repo_key)

        self.assertEqual(result.MessageResponseCode, result.ResponseCodes.OK)

        log.info('DataStore1 Push Complex addressbook to DataStore1: complete')




    @defer.inlineCallbacks
    def test_large_objects(self):

        n = 1000000

        rand = open('/dev/random','r')

        def _print_memory_usage():
            
            @brief Prints the memory usage of the container processes.
        
             Performs a ps command as a subprocess and retrieves the RSS and VSIZE of the 
             twistd container processes.
            
        
            
            log.info("Started the containers")
            ps_args = ["-o args,command,rss,vsize",  "-p", str(os.getpid())]
            #I'd rather not execute this through the shell, but the output from the command was truncated
            #when I did not set shell=True.
            p = subprocess.Popen(args=ps_args, executable="/bin/ps", stdout=subprocess.PIPE, shell=True)
            std_output = p.communicate()[0]
            #This should probably become a logging statement.
            print std_output
        
        
        @defer.inlineCallbacks
        def create_large_object():
            repo = yield self.wb1.workbench.create_repository(OPAQUE_ARRAY_TYPE)
            MB = 1024 * 124
            repo.root_object.value.extend(rand.read(2 *MB))

            repo.commit('Commit before send...')

            log.info('Repository size: %d bytes, array len %d' % (repo.__sizeof__(), len(repo.root_object.value)))

            defer.returnValue(repo)

        for i in range(1000):
            repo = yield create_large_object()

            result = yield self.wb1.workbench.push('datastore',repo)

            self.assertEqual(result.MessageResponseCode, result.ResponseCodes.OK)

            log.info('Datastore workbench size: %d' % self.ds1.workbench._repo_cache.total_size)
            log.info('Process workbench size: %d' % self.wb1.workbench._repo_cache.total_size)

            _print_memory_usage()
            self.wb1.workbench.clear_repository(repo)

        
         
        rand.close()



    @defer.inlineCallbacks
    def test_checkout_a_lot(self):


        for i in range(10):
            yield self.test_checkout_defaults()
            self.wb1.workbench.manage_workbench_cache('Test runner context!')

            for key, repo in self.wb1.workbench._repo_cache.iteritems():
                log.info('Repo Name - %s, size - %d, # of blobs - %d' % (key, repo.__sizeof__(), len(repo.index_hash)))

            log.info('Datastore workbench size: %d' % self.ds1.workbench._repo_cache.total_size)
            log.info('Process workbench size: %d' % self.wb1.workbench._repo_cache.total_size)

    """
