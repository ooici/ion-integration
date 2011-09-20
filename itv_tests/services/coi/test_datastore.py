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

from ion.services.coi.test import test_datastore as datastore_test
create_large_object = datastore_test.create_large_object


from ion.core.object import object_utils
OPAQUE_ARRAY_TYPE = object_utils.create_type_identifier(object_id=10016, version=1)


class CassandraBackedDataStoreTest(ItvTestCase):

    repetitions=200

    timeout = 600
    app_dependencies = [
            #("res/deploy/bootlevel4_local.rel", "id=1"),

            # Must create a keyspace (name==sysname) before starting the test if you use this method
            ("res/deploy/bootlevel4.rel", "id=1"),
                ]

    @defer.inlineCallbacks
    def setUp(self):
        yield self._start_container()
        self.proc = process.Process()
        yield self.proc.spawn()

        self.proc.op_fetch_blobs = self.proc.workbench.op_fetch_blobs


    @defer.inlineCallbacks
    def tearDown(self):
        yield self._stop_container()


    @defer.inlineCallbacks
    def test_large_objects(self):


        for i in range(self.repetitions):
            repo = yield create_large_object(self.proc.workbench)

            result = yield self.proc.workbench.push('datastore',repo)

            self.assertEqual(result.MessageResponseCode, result.ResponseCodes.OK)


            self.proc.workbench.clear_repository(repo)
            self.proc.workbench.manage_workbench_cache('Default Context')
            mem = yield pu.print_memory_usage()
            log.info(mem)


    @defer.inlineCallbacks
    def test_pull_object(self):

        repo = yield create_large_object(self.proc.workbench)

        result = yield self.proc.workbench.push('datastore',repo)

        self.repo_key = repo.repository_key

        for i in range(self.repetitions):

            result = yield self.proc.workbench.pull('datastore',self.repo_key)

            self.assertEqual(result.MessageResponseCode, result.ResponseCodes.OK)


            self.proc.workbench.manage_workbench_cache('Default Context')
            mem = yield pu.print_memory_usage()
            log.info(mem)
            log.info(self.proc.workbench_memory())
