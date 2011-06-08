#!/usr/bin/env python

"""
@file trial_tests/core/data/test/test_cassandra_store.py
@author Paul Hubbard
@author Dorian Raymer
@author David Stuebe
@author Matt Rodriguez
@test Service test of IStore Implementation

"""

import ion.util.ionlog
log = ion.util.ionlog.getLogger(__name__)
from uuid import uuid4

from twisted.trial import unittest
from twisted.internet import defer
from ion.test.iontest import IonTestCase

from ion.core.data import store
from ion.core.data import cassandra
from ion.core.data import index_store_service
from ion.core.data import store_service
from ion.core.data import storage_configuration_utility

from ion.core.data.test import test_store as import_test_store

# Import the workbench and the Persistent Archive Resource Objects!
from ion.core.object import workbench

from ion.core.object import object_utils
from ion.core.data.store import Query

from ion.core import ioninit
CONF = ioninit.config(__name__)



from ion.core.data.cassandra_bootstrap import CassandraStoreBootstrap, CassandraIndexedStoreBootstrap, CassandraSchemaProvider
from ion.core.data.cassandra_bootstrap import STORAGE_PROVIDER, PERSISTENT_ARCHIVE, IndexType


simple_password_type = object_utils.create_type_identifier(object_id=2502, version=1)
columndef_type = object_utils.create_type_identifier(object_id=2508, version=1)
column_family_type = object_utils.create_type_identifier(object_id=2507, version=1)
cassandra_cluster_type = object_utils.create_type_identifier(object_id=2504, version=1)
cassandra_keyspace_type = object_utils.create_type_identifier(object_id=2506, version=1)


class dummy(object):
    pass

class BootstrapStoreTest(dummy, import_test_store.IStoreTest):

    columns = []

    column_family = 'store_test_cf'


    @defer.inlineCallbacks
    def _setup_backend(self):


        uname = CONF.getValue('cassandra_username', None)
        pword = CONF.getValue('cassandra_password', None)
        storage_provider = CONF.getValue(STORAGE_PROVIDER,None)

        keyspace = 'store_test_ks'

        test_ks = storage_configuration_utility.base_ks_def.copy()
        test_ks['name'] = keyspace

        storage_conf = {
        STORAGE_PROVIDER:storage_provider,
        PERSISTENT_ARCHIVE:test_ks,
        }

        test_cf = storage_configuration_utility.base_cf_def.copy()
        test_cf['name'] = self.column_family
        test_cf['keyspace'] = keyspace
        test_cf['column_metadata'] = []


        test_ks['cf_defs']=[test_cf]


        for col in self.columns:
            test_col = storage_configuration_utility.base_col_def.copy()

            test_col['name'] = col
            test_col['index_type'] = IndexType.KEYS
            test_cf['column_metadata'].append(test_col)


        self.test_harness = CassandraSchemaProvider(uname,pword,storage_conf,error_if_existing=False)

        self.test_harness.connect()

        yield self.test_harness.run_cassandra_config()

        yield self.test_harness.client.truncate(self.column_family)

        store = self.create_store(uname, pword, storage_provider, keyspace, self.column_family)

        yield store.initialize()
        yield store.activate()


        defer.returnValue(store)


    def create_store(self, uname, pword, storage_provider, keyspace, column_family):

        return CassandraStoreBootstrap(uname, pword, storage_provider, keyspace, column_family)


    @defer.inlineCallbacks
    def tearDown(self):

        # Clear it, don't drop it...
        yield self.test_harness.client.truncate(self.column_family)

        self.test_harness.disconnect()

        try:
            yield self.ds.terminate()
        except Exception, ex:
            log.info("Exception raised in tearDown %s" % (ex,))


class CassandraStoreTest(BootstrapStoreTest):


    def create_store(self, uname, pword, storage_provider, keyspace, cf_name):

        ### This is a short cut to use resource objects without a process
        wb = workbench.WorkBench('No Process: Testing only')

        ### Create a persistence_technology resource - for cassandra a CassandraCluster object
        persistence_technology_repository, cassandra_cluster  = wb.init_repository(cassandra_cluster_type)

        # Set only one host and port in the host list for now
        cas_host = cassandra_cluster.hosts.add()

        cas_host.host = storage_provider['host']
        cas_host.port = storage_provider['port']

        ### Create a Persistent Archive resource - for cassandra a Cassandra KeySpace object
        persistent_archive_repository, cassandra_keyspace  = wb.init_repository(cassandra_keyspace_type)
        # only the name of the keyspace is required
        cassandra_keyspace.name = keyspace

        ### Create a Credentials resource - for cassandra a SimplePassword object
        cache_repository, simple_password  = wb.init_repository(simple_password_type)
        # only the name of the column family is required
        simple_password.username = uname or ''
        simple_password.password = pword or ''

        ### Create a Cache resource - for cassandra a ColumnFamily object
        cache_repository, column_family  = wb.init_repository(column_family_type)
        # only the name of the column family is required
        column_family.name = cf_name


        store = cassandra.CassandraStore(cassandra_cluster, \
                                         cassandra_keyspace, \
                                         simple_password, \
                                         column_family)

        return store

class BootstrapIndexedStoreTest(BootstrapStoreTest, import_test_store.IndexStoreTest):

    columns = import_test_store.IndexStoreTest.columns

    column_family = 'index_store_test_cf'


    def create_store(self, uname, pword, storage_provider, keyspace, column_family):

        return CassandraIndexedStoreBootstrap(uname, pword, storage_provider, keyspace, column_family)



class CassandraIndexedStoreTest(BootstrapIndexedStoreTest):



    def create_store(self, uname, pword, storage_provider, keyspace, cf_name):
        """
        @note The column_metadata in the cache is not correct. The column family on the
        server has a few more indexes.
        """

        ### This is a short cut to use resource objects without a process
        wb = workbench.WorkBench('No Process: Testing only')

        ### Create a persistence_technology resource - for cassandra a CassandraCluster object
        persistence_technology_repository, cassandra_cluster  = wb.init_repository(cassandra_cluster_type)

        # Set only one host and port in the host list for now
        cas_host = cassandra_cluster.hosts.add()

        cas_host.host = storage_provider['host']
        cas_host.port = storage_provider['port']

        ### Create a Persistent Archive resource - for cassandra a Cassandra KeySpace object
        persistent_archive_repository, cassandra_keyspace  = wb.init_repository(cassandra_keyspace_type)
        # only the name of the keyspace is required
        cassandra_keyspace.name = keyspace

        ### Create a Credentials resource - for cassandra a SimplePassword object
        cache_repository, simple_password  = wb.init_repository(simple_password_type)
        # only the name of the column family is required
        simple_password.username = uname or ''
        simple_password.password = pword or ''

        ### Create a Cache resource - for Cassandra a ColumnFamily object

        cache_repository, column_family  = wb.init_repository(column_family_type)
        # only the name of the column family is required
        column_family.name = cf_name

        self.cache = column_family
        self.cache_repository = cache_repository

        for col in self.columns:
            column = cache_repository.create_object(columndef_type)
            column.column_name = col
            column.validation_class = 'org.apache.cassandra.db.marshal.UTF8Type'
            #IndexType.KEYS is 0, and IndexType is an enum
            column.index_type = IndexType.KEYS


            link = self.cache.column_metadata.add()
            link.SetLink(column)


        store = cassandra.CassandraIndexedStore(cassandra_cluster, \
                                                cassandra_keyspace, \
                                                simple_password, \
                                                column_family)

        return store

    