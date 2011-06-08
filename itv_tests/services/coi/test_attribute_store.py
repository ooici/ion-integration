#!/usr/bin/env python

from iontest.iontest import ItvTestCase
from twisted.internet import defer
from ion.services.coi.attributestore import AttributeStoreClient

class AttributeStoreTest(ItvTestCase):
    app_dependencies = ["res/apps/attributestore.app"]  # start these apps prior to testing.

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

