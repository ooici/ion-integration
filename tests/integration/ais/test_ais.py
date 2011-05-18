

import ion.util.ionlog
from twisted.internet import defer

from ion.test.iontest import ItvTestCase

class TestAISProcecesses(ItvTestCase):
    app_dependencies = ["res/apps/datastore.app",
                       "res/apps/association.app",
                       "res/apps/resource_registry.app",
                       "res/apps/ems.app",
                       "res/apps/attributestore.app",
                       "res/apps/identity_registry.app",
                       "res/apps/pubsub.app",
                       "res/apps/scheduler.app",
                       "res/apps/dataset_controller.app",
                       "res/apps/app_integration.app"
                       ]
    
    @defer.inlineCallbacks
    def setUp(self):
        yield self._start_container()
        
    def test_instantiate(self):
        print "Startup worked"
        
    @defer.inlineCallbacks
    def tearDown(self):
        yield self._stop_container()    