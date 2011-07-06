#!/usr/bin/env python

"""
@file trial_tests/core/data/test/test_cassandra_init.py
@author Matt Rodriguez

"""

import ion.util.ionlog
log = ion.util.ionlog.getLogger(__name__)

from twisted.internet import defer

from ion.core.data import cassandra_bootstrap
from ion.core.data import storage_configuration_utility
from ion.core.data.storage_configuration_utility import PERSISTENT_ARCHIVE
from ion.test.iontest import IonTestCase

from telephus.cassandra.ttypes import InvalidRequestException


from ion.core import ioninit
CONF = ioninit.config(__name__)





class CassandraSchemaProviderTest(IonTestCase):
    """
    This class should probably be moved into the Cassanda init test module
    """

    keyspace = 'Hyphens-are-illegal-characters-for-keyspace-names'

    @defer.inlineCallbacks
    def setUp(self):
        yield self._start_container()

        self.uname = CONF.getValue('cassandra_username', None)
        self.pword = CONF.getValue('cassandra_password', None)

        storage_conf = storage_configuration_utility.get_cassandra_configuration(self.keyspace)
        storage_conf[PERSISTENT_ARCHIVE]["name"] = self.keyspace
        # Use a test harness cassandra client to set it up the way we want it for the test and tear it down
        test_harness = cassandra_bootstrap.CassandraSchemaProvider(self.uname, self.pword, storage_conf, error_if_existing=False)

        test_harness.connect()

        self.test_harness = test_harness
        
        try:
            yield self.test_harness.client.system_drop_keyspace(self.keyspace)
        except InvalidRequestException, ire:
            log.info("In the setUp method, could not drop a keyspace -- this is ok.")
            log.info(ire)



    @defer.inlineCallbacks
    def tearDown(self):

        try:
            yield self.test_harness.client.system_drop_keyspace(self.keyspace)
        except InvalidRequestException, ire:
            log.info("In the tearDown method, could not drop a keyspace -- this is ok.")
            log.info(ire)

        self.test_harness.disconnect()

        yield self._shutdown_processes()
        yield self._stop_container()

    @defer.inlineCallbacks
    def test_bad_keyspace_name(self):
        raised_exception = False
        try:
            #We need to change the keyspace name in each of the cf_defs to force the error
            storage_conf = storage_configuration_utility.get_cassandra_configuration(self.keyspace)
            for d  in storage_conf[PERSISTENT_ARCHIVE]["cf_defs"]:
                d["keyspace"] = self.keyspace
            #Set the keyspace name of the persistent archive    
            storage_conf[PERSISTENT_ARCHIVE]["name"] = self.keyspace
            yield self.test_harness.run_cassandra_config(storage_conf)
        except InvalidRequestException, ire:
            log.info(ire)
            ire2 = InvalidRequestException('Invalid keyspace name: ' + self.keyspace)
            self.failUnlessEqual(ire, ire2)
            raised_exception = True
            
        self.failUnlessTrue(raised_exception)



