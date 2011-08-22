from twisted.internet import defer

#from ion.util import procutils as pu
from ion.vandv.vandvbase import VVBase
import os, os.path, time

from ion.core.object.object_utils import sha1_to_hex
from ion.interact.int_observer import InteractionObserver
from ion.util.os_process import OSProcess
from ion.core.process.process import Process
from ion.services.coi.resource_registry.resource_client import ResourceClient
from ion.services.dm.distribution.events import DatasetSupplementAddedEventSubscriber, IngestionProcessingEventSubscriber

from ion.services.coi.datastore_bootstrap.ion_preload_config import SAMPLE_PROFILE_DATASET_ID

from ion.core.data.cassandra_bootstrap import CassandraStoreBootstrap, CassandraIndexedStoreBootstrap
from ion.core.data.storage_configuration_utility import get_cassandra_configuration, STORAGE_PROVIDER, PERSISTENT_ARCHIVE,BLOB_CACHE, COMMIT_CACHE

import binascii

from ion.core import ioninit
CONF = ioninit.config(__name__)


class VVDM16(VVBase):
    """
    [Test] The data catalog services shall be capable of adding metadata attributes
    Implemented using the resource registry and the common data model for science dataset resources.
    """

    @defer.inlineCallbacks
    def setup(self):

        # start full system
        yield self._start_itv(files=["itv_start_files/boot_level_4.itv",
                                     ])
        self.proc = Process()
        yield self.proc.spawn()
        self.rc = ResourceClient(proc=self.proc)


        uname = CONF.getValue('cassandra_username', None)
        pword = CONF.getValue('cassandra_password', None)

        self._storage_conf = get_cassandra_configuration()

        storage_provider = self._storage_conf[STORAGE_PROVIDER]
        keyspace = self._storage_conf[PERSISTENT_ARCHIVE]['name']

        self.commit_store = CassandraIndexedStoreBootstrap(uname, pword, storage_provider, keyspace, COMMIT_CACHE)
        self.blob_store = CassandraStoreBootstrap(uname, pword, storage_provider, keyspace, BLOB_CACHE)

        yield self.commit_store.initialize()
        yield self.commit_store.activate()

        yield self.blob_store.initialize()
        yield self.blob_store.activate()



    @defer.inlineCallbacks
    def s1_get_dataset(self):
        """
        1. Get an instance of a dataset of a dataset and print the global attributes
        """

        self.dset = yield self.rc.get_instance(SAMPLE_PROFILE_DATASET_ID)

        repo = self.dset.Repository

        print '==== Current Version of Dataset: ===='
        print '= Dataset ID: %s' % repo.repository_key
        print '= Dataset Branch: %s' % repo.current_branch_key()
        print '= Current Commit: %s' % sha1_to_hex(repo.commit_head.MyId)
        print '= Current number of attributes in dataset: %d' % len(self.dset.root_group.attributes)
        print '====================================='

        #print self.dset.root_group.attributes.PPrint(name='Attribute')


    def s2_add_dataset_attribute(self):
        """
        2. Add a new global attribute to the dataset and print the attributes again
        """
        group = self.dset.root_group
        attr = group.AddAttribute('NewAttribute', group.DataType.STRING, 'ASA OOICI team kicks ass!')

        print 'Added new attribute:'
        print attr.PPrint()

        self.attr = attr

        repo = self.dset.Repository
        repo.commit('Commiting dataset changes for VV DM16 step 2')

        print '==== New Attribute ID and Content: ===='
        print '= Attribute CASRef: %s' % sha1_to_hex(self.attr.MyId)
        se = repo.index_hash.get(self.attr.MyId)
        print 'Attribute blob: %s' % binascii.b2a_base64(se.value)

        print '= Attribute CASRef: %s' % sha1_to_hex(self.attr.array.MyId)
        se = repo.index_hash.get(self.attr.array.MyId)
        print 'Attribute array blob: %s' % binascii.b2a_base64(se.value)
        print '======================================='


    @defer.inlineCallbacks
    def s3_persist_dataset_changes(self):
        """
        3. Push the dataset to the datastore for persistence and print the keys of the new version and the new attributes
        """

        yield self.rc.put_instance(self.dset)
        repo = self.dset.Repository

        print '==== New Version of Dataset: ===='
        print '= Dataset ID: %s' % repo.repository_key
        print '= Dataset Branch: %s' % repo.current_branch_key()
        print '= Current Commit: %s' % sha1_to_hex(repo.commit_head.MyId)
        print '= Parent Commit: %s' % sha1_to_hex(repo.commit_head.parentrefs[0].commitref.MyId)
        print '================================='



    @defer.inlineCallbacks
    def s4_extract_and_examine_persisted_elements(self):
        """
        4. Get the blobs from cassandra using a separate connection to show they were persisted
        """
        repo = self.dset.Repository


        # Get the blobs stored in cassandra directly and print to screen
        print '==== Cassandra Content: ===='
        blob = yield self.blob_store.get(self.attr.MyId)
        print 'Attribute blob: %s' % binascii.b2a_base64(blob)

        blob = yield self.blob_store.get(self.attr.MyId)
        print 'Attribute array blob: %s' % binascii.b2a_base64(blob)

        blob = yield self.commit_store.get(repo.commit_head.MyId)
        print 'Commit blob: %s' % binascii.b2a_base64(blob)

        print '============================'


    def s5_show_previous_versions(self):
        """
        5. Show the commit log for the dataset
        """
        repo = self.dset.Repository

        print 'Commit History:'
        print repo.list_parent_commits()


    @defer.inlineCallbacks
    def teardown(self):

        print 'Tearing Down Cassandra Column Families'
        # Don't let the test script persist anything between tests.
        yield self.blob_store.client.truncate(self.blob_store._cache_name)
        yield self.commit_store.client.truncate(self.commit_store._cache_name)

        self.blob_store.terminate()
        self.commit_store.terminate()

        yield VVBase.teardown(self)

        