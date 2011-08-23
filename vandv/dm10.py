from twisted.internet import defer

#from ion.util import procutils as pu
from ion.vandv.vandvbase import VVBase
import os, os.path, tempfile

from ion.core.process.process import Process
from ion.services.coi.resource_registry.resource_client import ResourceClient
from ion.util.os_process import OSProcess
from ion.core.object import object_utils

BLOB_TYPE = object_utils.create_type_identifier(object_id=2540, version=1)
FILENAME = "vandv/dm10/MIT_Concert_Choir_-_01_-_O_Fortuna.mp3"

class VVDM10(VVBase):
    """
    [Demonstration]
    L4-DM-RQ-77 The persistent archive services shall be data format agnostic
    https://confluence.oceanobservatories.org/display/syseng/R1+DM+Verification+Procedure+10
    """

    @defer.inlineCallbacks
    def setup(self):

        # start full system
        self._first_run = yield self._start_itv(files=["itv_start_files/boot_level_4_local.itv"])

        # anon process
        self._proc = Process(spawnargs={'process-name':'VVDM10'})
        yield self._proc.spawn()

        self._rc = ResourceClient(proc=self._proc)

    @defer.inlineCallbacks
    def s1_show_original_mp3(self):
        """
        1. Play source MP3 and show md5sum/ls
        """

        osp = OSProcess("/bin/ls", spawnargs=["-l", "vandv/dm10"])
        lso = yield osp.spawn()

        print "FILE:", "\n".join(lso['outlines'])

        osp = OSProcess("/sbin/md5", spawnargs=[FILENAME])
        md5o = yield osp.spawn()

        print "MD5:", "\n".join(md5o['outlines'])

        osp = OSProcess("/usr/bin/open", spawnargs=[FILENAME])
        yield osp.spawn()

    @defer.inlineCallbacks
    def s2_store_in_datastore(self):
        """
        2. Store the MP3 in the datastore
        """

        song = yield self._rc.create_instance(BLOB_TYPE, "MITSong", "OFortuna")

        try:
            f = open(FILENAME, "rb")
        except IOError, ex:
            print "PROBLEM OPENING MP3", str(ex)
            defer.returnValue(None)

        bytes_buffer = f.read()
        song.blob = bytes_buffer

        print "Putting song into registry"
        yield self._rc.put_instance(song, "Persisting song resource")

        self._resource_id = self._rc.reference_instance(song)
        print "RESOURCE ID IS:", str(self._resource_id)

    @defer.inlineCallbacks
    def s3_retrieve_from_datastore(self):
        """
        3. Retrieve from datastore into a temporary file, show it, play it
        """

        song = yield self._rc.get_instance(self._resource_id)
        song_buffer = song.blob

        fno, self._fpath = tempfile.mkstemp(suffix=".mp3")
        print "Writing mp3 to temp file:", self._fpath
        f = os.fdopen(fno, 'w+b')
        f.write(song_buffer)
        f.close()

        osp = OSProcess("/bin/ls", spawnargs=["-l", self._fpath])
        lso = yield osp.spawn()

        print "FILE COPY:", "\n".join(lso['outlines'])

        osp = OSProcess("/sbin/md5", spawnargs=[self._fpath])
        md5o = yield osp.spawn()

        print "MD5 COPY:", "\n".join(md5o['outlines'])

        osp = OSProcess("/usr/bin/open", spawnargs=[self._fpath])
        yield osp.spawn()

    def s4_cleanup_temp_file(self):
        """
        4. Remove temporary mp3 from disk
        """
        print "Removing temporary file:", self._fpath
        os.unlink(self._fpath)

