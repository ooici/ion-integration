"""
Created on Jun 15, 2011

@author: Matt Rodriguez
This is for the verification test L4-CI-DM-RQ-77
@note I think this is the only OOI test that plays an mp3
"""


import os
import subprocess

from twisted.internet import defer
import ion.util.ionlog
log = ion.util.ionlog.getLogger(__name__)

from ion.core.object import object_utils
from ion.core.process.process import Process

from ion.test.iontest import IonTestCase

from ion.services.coi.resource_registry.resource_client import ResourceClient

BLOB_TYPE = object_utils.create_type_identifier(object_id=2540, version=1)
class MusicVerificationTest(IonTestCase):
    
    @defer.inlineCallbacks
    def setUp(self):
        yield self._start_container()
        services = [
            {'name':'ds1','module':'ion.services.coi.datastore','class':'DataStoreService'},
            {'name':'resource_registry1','module':'ion.services.coi.resource_registry.resource_registry','class':'ResourceRegistryService',
             'spawnargs':{'datastore_service':'datastore'}}]
        sup = yield self._spawn_processes(services)

        self.rc = ResourceClient(proc=sup)
        proc2 = Process()
        yield proc2.initialize()
        self.proc2 = proc2
        self.rc2 = ResourceClient(proc=self.proc2)
        self.sup = sup
        
    @defer.inlineCallbacks
    def test_put_and_get(self):
        song = yield self.rc.create_instance(BLOB_TYPE, "WagnerSong", "Ride of the Valkyries")
        print os.getcwd()
        f = open("../data/zoidberg.mp3", "rb")
        bytes_buffer = f.read()
        
        song.blob = bytes_buffer
    
        yield self.rc.put_instance(song, "Persisting song resource")
        reference = self.rc.reference_instance(song)
        
        
        
        get_back_song = yield self.rc2.get_instance(reference)
        buf = get_back_song.blob
        fout = open("../data/zoidberg_out.mp3", "wb")
        fout.write(buf)
        subprocess.Popen(["/usr/bin/afplay", "../data/zoidberg_out.mp3"])
        
    @defer.inlineCallbacks
    def tearDown(self):
        
        yield self._shutdown_processes()
        yield self._stop_container()