#!/usr/bin/env python

"""
@file ion/play/test/test_hello_resource.py
@test ion.play.hello_resource Example unit tests for sample resource code.
@author David Stuebe
"""
import tempfile

import ion.util.ionlog
log = ion.util.ionlog.getLogger(__name__)

from twisted.internet import defer

from ion.core.process import process
from ion.test.iontest import IonTestCase
from ion.services.coi.resource_registry import resource_client
from ion.core.messaging.message_client import MessageClient
from ion.services.coi.datastore import ION_DATASETS_CFG, PRELOAD_CFG
from ion.util.procutils import asleep

from ion.services.dm.distribution.events import ScheduleEventPublisher

# Message types
from ion.services.dm.inventory.dataset_controller import  SCHEDULE_TYPE_DSC_RSYNC

from ion.services.dm.inventory.ncml_generator import clear_ncml_files, check_for_ncml_files


from ion.core import ioninit
CONF = ioninit.config(__name__)


class DatasetControllerTest(IonTestCase):
    """
    Testing example hello resource service.
    This example shows how it is possible to create and send resource requests.
    """

    #noinspection PyUnusedLocal
    @defer.inlineCallbacks
    def setUp(self):
        yield self._start_container()
        
        tempdir = tempfile.mkdtemp()
        
        services = [

            {'name':'ds1','module':'ion.services.coi.datastore','class':'DataStoreService',
             'spawnargs':{PRELOAD_CFG:{ION_DATASETS_CFG:True},}
                },

            {'name':'association_service',
             'module':'ion.services.dm.inventory.association_service',
             'class':'AssociationService'
              },

            {'name':'resource_registry1','module':'ion.services.coi.resource_registry.resource_registry','class':'ResourceRegistryService',
             'spawnargs':{'datastore_service':'datastore'}},

            {'name': 'scheduler', 'module': 'ion.services.dm.scheduler.scheduler_service',
             'class': 'SchedulerService'},

            {'name':'dataset_controller',
             'module':'ion.services.dm.inventory.dataset_controller',
             'class':'DataSetController',
             'spawnargs': {'do-init' : False, 'ncml_path': tempdir }},
        ]


        sup = yield self._spawn_processes(services)
        self.sup = sup
        # Creat an anonymous process for the tests
        self.proc = process.Process()
        yield self.proc.spawn()

        self.mc = MessageClient(proc=self.proc)
        self.rc = resource_client.ResourceClient(proc=self.proc)


    @defer.inlineCallbacks
    def tearDown(self):
        yield self._shutdown_processes()
        yield self._stop_container()



    @defer.inlineCallbacks
    def test_create_and_rsync_manually(self):

        dataset_controller_id = yield self.sup.get_child_id('dataset_controller')
        log.debug('Process ID:' + str(dataset_controller_id))
        dataset_controller= self._get_procinstance(dataset_controller_id)

        clear_ncml_files(dataset_controller.ncml_path)
        self.failIf(check_for_ncml_files(dataset_controller.ncml_path))

        yield dataset_controller.do_ncml_sync()

        self.failUnless(check_for_ncml_files(dataset_controller.ncml_path))


    @defer.inlineCallbacks
    def test_create_and_rsync_fire_message(self):

        dataset_controller_id = yield self.sup.get_child_id('dataset_controller')
        log.debug('Process ID:' + str(dataset_controller_id))
        dataset_controller= self._get_procinstance(dataset_controller_id)

        clear_ncml_files(dataset_controller.ncml_path)
        self.failIf(check_for_ncml_files(dataset_controller.ncml_path))

        pub = ScheduleEventPublisher(process=self.proc)
        yield pub.create_and_publish_event(origin=SCHEDULE_TYPE_DSC_RSYNC,
                                          task_id=dataset_controller.task_id)

        log.info("dataset_controller.ncml_path %s" % (dataset_controller.ncml_path))
        
        #The NCML files will be at the path, after the scheduled event has happened
        while not check_for_ncml_files(dataset_controller.ncml_path):
            yield asleep(2)


