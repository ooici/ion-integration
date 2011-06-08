#!/usr/bin/env python

"""
@file inttest_bootlevel4_local.py
@author Dave Foster <dfoster@asascience.com>
@test Bootlevel 4 ready checks (local services only).
"""

import ion.util.ionlog
from twisted.internet import defer
from iontest.iontest import ItvTestCase
from ion.core import ioninit
from ion.core.process.process import Process
from ion.services.coi.datastore_bootstrap.ion_preload_config import ION_PREDICATES, ION_RESOURCE_TYPES, ION_IDENTITIES
from ion.services.coi.datastore_bootstrap.ion_preload_config import NAME_CFG, CONTENT_ARGS_CFG, PREDICATE_CFG
from ion.services.coi.datastore import ID_CFG

log = ion.util.ionlog.getLogger(__name__)
CONF = ioninit.config(__name__)

class Bootlevel4LocalReadyTest(ItvTestCase):

    app_dependencies = ["res/deploy/bootlevel4_local.rel"]

    @defer.inlineCallbacks
    def setUp(self):
        yield self._start_container()

    @defer.inlineCallbacks
    def tearDown(self):
        yield self._stop_container()

    @defer.inlineCallbacks
    def test_all_services(self):
        p = Process()
        yield p.spawn()

        for servicename in ['datastore', 'association_service', 'resource_registry']:
            (content, headers, msg) = yield p.rpc_send(p.get_scoped_name('system', servicename), 'ping', {})
            # if timeout, will just fail the test

        # perform basic datastore level tests to make sure required things are there
        defaults={}
        defaults.update(ION_RESOURCE_TYPES)
        defaults.update(ION_IDENTITIES)

        for key, value in defaults.items():

            repo_name = value[ID_CFG]

            c_args = value.get(CONTENT_ARGS_CFG)
            if c_args and not c_args.get('filename'):
                break



            result = yield p.workbench.pull('datastore',repo_name)
            self.assertEqual(result.MessageResponseCode, result.ResponseCodes.OK)

            repo = p.workbench.get_repository(repo_name)

            # Check that we got back both branches!
            default_obj = yield repo.checkout(branchname='master')

            self.assertEqual(default_obj.name, value[NAME_CFG])


        for key, value in ION_PREDICATES.items():

            repo_name = value[ID_CFG]

            result = yield p.workbench.pull('datastore',repo_name)
            self.assertEqual(result.MessageResponseCode, result.ResponseCodes.OK)

            repo = p.workbench.get_repository(repo_name)

            # Check that we got back both branches!
            default_obj = yield repo.checkout(branchname='master')

            self.assertEqual(default_obj.word, value[PREDICATE_CFG])

