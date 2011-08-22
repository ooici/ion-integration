from twisted.internet import defer

#from ion.util import procutils as pu
from ion.vandv.vandvbase import VVBase
import os, os.path

from ion.core.process.process import Process
from ion.interact.mscweb import MSCWebProcess
from ion.util.os_process import OSProcess
from ion.services.dm.distribution.events import DatasetSupplementAddedEventSubscriber, IngestionProcessingEventSubscriber

import ion.util.ionlog
log = ion.util.ionlog.getLogger(__name__)

class VVDM7(VVBase):
    """
    [Demonstration] The dynamic data distribution services shall support 
                    multiple data messages on a given data stream.
    [Demonstration] The dynamic data distribution services shall associate
                    data streams with data resources.
    """

    @defer.inlineCallbacks
    def setup(self):

        # start full system
        yield self._start_itv(files=["itv_start_files/boot_level_4_local.itv",
                                     "itv_start_files/boot_level_5.itv",
                                     "itv_start_files/boot_level_6.itv",
                                     "itv_start_files/boot_level_7.itv",
                                     "itv_start_files/boot_level_8.itv",
                                     "itv_start_files/boot_level_9.itv",
                                     "itv_start_files/4x_boot_level_10.itv"])

        self._proc = Process(spawnargs={'proc-name':'vvdm7_proc'})
        yield self._proc.spawn()

        # supplement added subscriber - we yield on updates here
        self._def_sup_added = defer.Deferred()  # gets called back every time we get one, we must manually reset

        self._sub = DatasetSupplementAddedEventSubscriber(process=self._proc)
        self._sub.ondata = lambda msg: self._def_sup_added.callback(msg)

        yield self._proc.register_life_cycle_object(self._sub)

        # subscriber so we can just see something is happening
        self._ingest_sub = IngestionProcessingEventSubscriber(process=self._proc)
        def _print_ingest(dat):
            print "INGEST PROCESSING:", dat['content'].additional_data.processing_step

        self._ingest_sub.ondata = _print_ingest

        yield self._proc.register_life_cycle_object(self._ingest_sub)

        self._mscweb = MSCWebProcess()
        yield self._mscweb.spawn()

        # open a browser
        openosp = OSProcess(binary="/usr/bin/open", spawnargs=["http://localhost:9999"])
        yield openosp.spawn()

    @defer.inlineCallbacks
    def _ingest_dataset(self):

        ijr = os.path.join(os.getcwd().rsplit("/", 1)[0], 'ioncore-java-runnables')
        dsreg = OSProcess(binary=os.path.join(ijr, 'dataset_registration'), startdir=ijr, spawnargs=[os.path.join(os.getcwd(), "vandv", "dm7", "ndbc_sos-44014_winds.dsreg")])
        fin = yield dsreg.spawn()

        # pull out dataset id
        for lines in fin['outlines']:
            for line in lines.split("\n"):
                if "data_set_id: " in line:
                    _, dsid = line.split(" ")
                    defer.returnValue(dsid.strip().strip("\""))
                    break

        defer.returnValue(None)

    @defer.inlineCallbacks
    def s1_ingest_initial_dataset(self):
        """
        1. Instruct one dataset agent to ingest initial dataset
        """

        self._dataset_id = yield self._ingest_dataset()

        yield self._def_sup_added
        self._def_sup_added = defer.Deferred()

        print "We got", self._dataset_id

    @defer.inlineCallbacks
    def s2_generate_update(self):
        """
        2. Instruct next dataset agent to grab any supplemental data
        """
        ijr = os.path.join(os.getcwd().rsplit("/", 1)[0], 'ioncore-java-runnables')
        dsreg = OSProcess(binary=os.path.join(ijr, 'generate_update_event'), startdir=ijr, spawnargs=[self._dataset_id])
        yield dsreg.spawn()

        yield self._def_sup_added
        self._def_sup_added = defer.Deferred()

    @defer.inlineCallbacks
    def s3_generate_update_2(self):
        """
        3. Instruct next dataset agent to grab any supplemental data (again)
        """
        ijr = os.path.join(os.getcwd().rsplit("/", 1)[0], 'ioncore-java-runnables')
        dsreg = OSProcess(binary=os.path.join(ijr, 'generate_update_event'), startdir=ijr, spawnargs=[self._dataset_id])
        yield dsreg.spawn()

        yield self._def_sup_added
        self._def_sup_added = defer.Deferred()

    @defer.inlineCallbacks
    def s4_show_msc(self):
        """
        4. Show an MSC of what just happened
        """
        pass
