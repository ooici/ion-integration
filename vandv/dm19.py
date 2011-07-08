from twisted.internet import defer

#from ion.util import procutils as pu
from ion.vandv.vandvbase import VVBase
import os, os.path, time

from ion.interact.int_observer import InteractionObserver
from ion.core.process.process import Process
from ion.services.coi.resource_registry.resource_client import ResourceClient
from ion.util.os_process import OSProcess, OSProcessError
from ion.services.dm.distribution.events import DatasetSupplementAddedEventSubscriber, IngestionProcessingEventSubscriber

class VVDM19(VVBase):
    """
    [Test] The persistent archive services shall preserve all associations between data and metadata.
    """

    @defer.inlineCallbacks
    def setup(self):

        # start full system
        self._first_run = yield self._start_itv(files=["itv_start_files/boot_level_4.itv",
                                                       "itv_start_files/boot_level_5.itv",
                                                       "itv_start_files/boot_level_6.itv",
                                                       "itv_start_files/boot_level_7.itv",
                                                       "itv_start_files/boot_level_8.itv",
                                                       "itv_start_files/boot_level_9.itv",
                                                       "itv_start_files/boot_level_10.itv"])

        # anon process
        self._proc = Process(spawnargs={'process-name':'VVDM19'})
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

        self._rc = ResourceClient(proc=self._proc)

    @defer.inlineCallbacks
    def _ingest_dataset(self):

        ijr = os.path.join(os.getcwd().rsplit("/", 1)[0], 'ioncore-java-runnables')
        dsreg = OSProcess(binary=os.path.join(ijr, 'dataset_registration'), startdir=ijr, spawnargs=[os.path.join(os.getcwd(), "vandv", "dm19", "ndbc_sos-44014_winds.dsreg")])
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
        1. Instruct dataset agent to ingest dataset
        """

        self._dataset_id = yield self._ingest_dataset()

        yield self._def_sup_added
        self._def_sup_added = defer.Deferred()

        print "We got", self._dataset_id

    @defer.inlineCallbacks
    def s2_teardown_system(self):
        """
        2. Tell entire system to shutdown.
        """

        pcount = 0
        psosp = OSProcess(binary="/bin/ps", startargs=["aux"])
        res = yield psosp.spawn()

        for lines in res['outlines']:
            for line in lines.split('\n'):
                if "twistd" in line:
                    pcount += 1
        print "twistd processes: ", pcount

        try:
            yield self._first_run.close(timeout=10)
        except OSProcessError, ex:
            pass

        pcount = 0
        psosp = OSProcess(binary="/bin/ps", startargs=["aux"])
        res = yield psosp.spawn()

        for lines in res['outlines']:
            for line in lines.split('\n'):
                if "twistd" in line:
                    pcount += 1
        print "twistd processes: ", pcount

    @defer.inlineCallbacks
    def s3_restart_system(self):
        """
        3. Restart the system
        """

        print "Restarting system"
        # start full system
        self._second_run = yield self._start_itv(files=["itv_start_files/boot_level_4.itv",
                                                        "itv_start_files/boot_level_5.itv",
                                                        "itv_start_files/boot_level_6.itv",
                                                        "itv_start_files/boot_level_7.itv",
                                                        "itv_start_files/boot_level_8.itv",
                                                        "itv_start_files/boot_level_9.itv",
                                                        "itv_start_files/boot_level_10.itv"])
        print "Restarted"

    @defer.inlineCallbacks
    def s4_query_dataset(self):
        """
        4. Query RR for previously ingested dataset
        """
        dsr = yield self._rc.get_instance(self._dataset_id)

        print "we got", dsr
