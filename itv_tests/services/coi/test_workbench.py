#!/usr/bin/env python

"""
@file ion/services/coi/test/test_datastore.py
@author David Stuebe
"""


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


from ion.services.coi.test import test_datastore as datastore_test
create_large_object = datastore_test.create_large_object

from telephus.cassandra.ttypes import InvalidRequestException


from ion.core.object import object_utils
OPAQUE_ARRAY_TYPE = object_utils.create_type_identifier(object_id=10016, version=1)


class WorkBenchTest(ItvTestCase):

    repetitions = 20
    timeout = 600
    app_dependencies = [
                ("res/apps/workbench.app", "id=1"),
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

            result = yield self.proc.workbench.push('workbench',repo)

            self.assertEqual(result.MessageResponseCode, result.ResponseCodes.OK)


            self.proc.workbench.manage_workbench_cache('Test runner context!')
            log.info('Memory use is expected to grow in one process only - the workbench app does not have persistent backend')
            mem = yield pu.print_memory_usage()
            log.info(mem)
            log.info("Local Workbench: %s" % self.proc.workbench_memory())


    @defer.inlineCallbacks
    def test_pull_object(self):


        repo = yield create_large_object(self.proc.workbench)

        result = yield self.proc.workbench.push('workbench',repo)

        self.repo_key = repo.repository_key

        for i in range(self.repetitions):

            result = yield self.proc.workbench.pull('workbench',self.repo_key)

            self.assertEqual(result.MessageResponseCode, result.ResponseCodes.OK)

            self.proc.workbench.manage_workbench_cache('Test runner context!')
            mem = yield pu.print_memory_usage()
            log.info(mem)
            print self.proc.workbench_memory()
