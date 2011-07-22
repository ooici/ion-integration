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
from ion.core.process import process

from iontest.iontest import ItvTestCase

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


from ion.core.object import object_utils
OPAQUE_ARRAY_TYPE = object_utils.create_type_identifier(object_id=10016, version=1)


class CassandraBackedDataStoreTest(ItvTestCase):


    timeout = 600
    app_dependencies = [
                ("res/deploy/bootlevel4_local.rel", "id=1"),
                ]

    @defer.inlineCallbacks
    def setUp(self):
        yield self._start_container()
        self.proc = process.Process()
        yield self.proc.spawn()

        self.proc.op_fetch_blobs = self.proc.workbench.op_fetch_blobs

        repo = yield self.create_large_object()

        result = yield self.proc.workbench.push('datastore',repo)

        self.repo_key = repo.repository_key



    @defer.inlineCallbacks
    def tearDown(self):
        yield self._stop_container()


    @defer.inlineCallbacks
    def create_large_object(self):

        rand = open('/dev/random','r')

        repo = yield self.proc.workbench.create_repository(OPAQUE_ARRAY_TYPE)
        MB = 1024 * 124
        repo.root_object.value.extend(rand.read(2 *MB))

        repo.commit('Commit before send...')

        log.info('Repository size: %d bytes, array len %d' % (repo.__sizeof__(), len(repo.root_object.value)))

        rand.close()


        defer.returnValue(repo)

    @defer.inlineCallbacks
    def test_large_objects(self):


        for i in range(300):
            repo = yield self.create_large_object()

            result = yield self.proc.workbench.push('datastore',repo)

            self.assertEqual(result.MessageResponseCode, result.ResponseCodes.OK)

            print pu.print_memory_usage()
            self.proc.workbench.clear_repository(repo)



    @defer.inlineCallbacks
    def test_pull_object(self):

        for i in range(4):

            result = yield self.proc.workbench.pull('datastore',self.repo_key)

            self.assertEqual(result.MessageResponseCode, result.ResponseCodes.OK)

            print pu.print_memory_usage()
            self.proc.workbench.manage_workbench_cache('Test runner context!')
            print self.proc.workbench_memory()
