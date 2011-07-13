"""
Created on Jul 8, 2011

@author: mateo
"""
import ion.util.ionlog
log = ion.util.ionlog.getLogger(__name__)

from twisted.internet import defer

from ion.core import ioninit
CONF = ioninit.config(__name__)

from ion.integration.ais.notification_alert_service import NotificationAlertServiceClient
from ion.integration.ais.app_integration_service import AppIntegrationServiceClient

from ion.core.data import cassandra_bootstrap
from ion.core.data import storage_configuration_utility
from telephus.cassandra.ttypes import InvalidRequestException

from ion.core.data.storage_configuration_utility import BLOB_CACHE, COMMIT_CACHE,  PERSISTENT_ARCHIVE
from ion.services.coi.datastore_bootstrap.ion_preload_config import ION_DATASETS_CFG, ION_AIS_RESOURCES_CFG, PRELOAD_CFG

from ion.integration.ais.test import test_notification_alert as import_test_notification_alert

class CassandraBackedNotificationAlertTest(import_test_notification_alert.NotificationAlertTest):
    
    username = CONF.getValue('cassandra_username', None)
    password = CONF.getValue('cassandra_password', None)
    
    
    cass_services = [
                
        {'name':'ds1','module':'ion.services.coi.datastore','class':'DataStoreService',
         'spawnargs':{COMMIT_CACHE:'ion.core.data.cassandra_bootstrap.CassandraIndexedStoreBootstrap',
                      BLOB_CACHE:'ion.core.data.cassandra_bootstrap.CassandraStoreBootstrap',
                      PRELOAD_CFG:{ION_DATASETS_CFG:True, ION_AIS_RESOURCES_CFG:True},
                      "username": username,
                      "password": password }
        },  
        #I've hard coded the column family name below. 
        #It's possible to get the name out of the storage_conf, but I have to know the name of the column 
        #family in order to get the name of the column family. 
        {'name':'notification_alert',
         'module':'ion.integration.ais.notification_alert_service',
         'class':'NotificationAlertService',
            
            'spawnargs':{"index_store_class": 'ion.core.data.cassandra_bootstrap.CassandraIndexedStoreBootstrap',
                         "keyspace": "sysname",
                         "column_family":  "notification_alert_service",
                         "cassandra_username": username,
                         "cassandra_password": password
                         }
            },

        ]
    #Remove the in memory datastore services, replace with CassandraBacked services    
    filter_func = lambda service: service["class"] != 'NotificationAlertService' and service["class"] != 'DataStoreService'
    services = filter(filter_func, import_test_notification_alert.NotificationAlertTest.services )
    services.extend(cass_services)
    

    @defer.inlineCallbacks
    def setUp(self):
        yield self._start_container()
        print self.services
        
        storage_conf = storage_configuration_utility.get_cassandra_configuration()

        self.keyspace = storage_conf[PERSISTENT_ARCHIVE]["name"]
        
        test_harness = cassandra_bootstrap.CassandraSchemaProvider(self.username, self.password, storage_conf, error_if_existing=False)

        test_harness.connect()

        self.test_harness = test_harness
        
        try:
            yield self.test_harness.client.system_drop_keyspace(self.keyspace)
        except InvalidRequestException, ire:
            log.info('No Keyspace to remove in setup: ' + str(ire))

        yield test_harness.run_cassandra_config()
        
        sup = yield self._spawn_processes(self.services)
        self.sup = sup
        self.nac = NotificationAlertServiceClient(proc=sup)
        self.aisc = AppIntegrationServiceClient(proc=sup) 
        
    @defer.inlineCallbacks
    def tearDown(self):
        log.info("In tearDown")
        try:
            yield self.test_harness.client.system_drop_keyspace(self.keyspace)
        except InvalidRequestException, ire:
            log.info('No Keyspace to remove in teardown: ' + str(ire))


        self.test_harness.disconnect()
        
        yield self._shutdown_processes()
        yield self._stop_container()
   
        