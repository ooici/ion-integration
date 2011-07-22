#!/usr/bin/env python

"""
@file iontest/iontest.py
@author Michael Meisinger
@author Matt Rodriguez
@brief test case for ION integration and system test cases (and some unit tests)
"""
import os
import subprocess


import ion.util.ionlog
log = ion.util.ionlog.getLogger(__name__)
from ion.test.iontest import IonTestCase

from ion.core import ioninit

# The following modules must be imported here, because they load config
# files. If done while in test, it does not work!

CONF = ioninit.config(__name__)


class ItvTestCase(IonTestCase):
    """
    Integration testing base class for use with trial/itv_trial.

    Tests a fully spawned system, either via CEI bootstrapping, or a locally spawned system via itv_trial.

    Read more at:
        https://confluence.oceanobservatories.org/display/CIDev/ITV+R1C3+Integration+Test+Framework

    To use, derive your test from ion.test.ItvTestCase and fill in the services class
    attribute with a list of apps your test needs. Apps are relative to the current working
    directory and typically reside in the res/apps subdir of ioncore-python.

    Example:

        class AttributeStoreTest(ItvTestCase):
            services = ["res/apps/attributestore.app"]  # start these apps prior to testing.

            @defer.inlineCallbacks
            def setUp(self):
                yield self._start_container()

            @defer.inlineCallbacks
            def tearDown(self):
                yield self._stop_container()

            @defer.inlineCallbacks
            def test_set_attr(self):
                asc = AttributeStoreClient()
                yield asc.put("hi", "hellothere")

                res = yield asc.get("hi")
                self.failUnless(res == "hellothere")

            @defer.inlineCallbacks
            def test_set_attr2(self):
                # "hi" is still set here, but only if test_set_attr is run first, be careful
                asc = AttributeStoreClient()
                res = yield asc.get("hi")
                self.failUnless(res == "hellothere")

    Important points:
    - The sysname parameter is required to get all the services and tests running on the same
      system. itv_trial takes care of this for you, but if you want to deploy these tests vs
      a CEI spawned environment, you must set the environment variable ION_TEST_CASE_SYSNAME
      to be the same as the sysname the CEI environment was spawned with.

    """
    services = []
    
