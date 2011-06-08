#!/usr/bin/env python

"""
@file inttest_association.py
@author Dave Foster <dfoster@asascience.com>
@test 
"""

import ion.util.ionlog
from twisted.internet import defer
from twisted.trial import unittest
from iontest.iontest import ItvTestCase
from ion.core import ioninit

#from ion.services.dm.inventory.test.test_association_service import AssociationServiceTest
from ion.services.dm.inventory.test import test_association_service as ioncore_python_assoc_test

log = ion.util.ionlog.getLogger(__name__)
CONF = ioninit.config(__name__)

class AssociationServiceIntegrationTest(ItvTestCase,ioncore_python_assoc_test.AssociationServiceTest):

    app_dependencies = ["res/deploy/events.rel"]
    services = []       # blank out services from base class so setUp doens't start them.

    @defer.inlineCallbacks
    def setUp(self):
        self._skip_test_msg = "Skipping this test because it assumes the backend data is not persisted."
        yield ioncore_python_assoc_test.AssociationServiceTest.setUp(self)

    def test_get_association_one(self):
        raise unittest.SkipTest(self._skip_test_msg)

    def test_association_by_type_and_lcs(self):
        raise unittest.SkipTest(self._skip_test_msg)

    def test_association_subject_predicate_updated_object(self):
        raise unittest.SkipTest(self._skip_test_msg)

    def test_association_false(self):
        raise unittest.SkipTest(self._skip_test_msg)

