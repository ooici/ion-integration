from twisted.internet import defer

#from ion.util import procutils as pu
from ion.vandv.vandvbase import VVBase
import os, os.path, time

from ion.interact.int_observer import InteractionObserver
from ion.util.os_process import OSProcess
from ion.services.dm.distribution.events import DatasetSupplementAddedEventSubscriber, IngestionProcessingEventSubscriber

class VVDM16(VVBase):
    """
    [TEST]
    L4-DM-RQ-183 The data ingestion services shall manage ingestion of a data set
    https://confluence.oceanobservatories.org/display/syseng/R1+DM+Verification+Procedure+16
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
                                     "itv_start_files/4x_ingestion.itv",        # 5x ingestions total (1 from level 9)
                                     "itv_start_files/5x_boot_level_10.itv"])   # 5x jaw

        # message observer - spawning here means we don't have to listen to startup stuff
        self._mo = InteractionObserver()
        yield self._mo.spawn()

        # supplement added subscriber - we yield on updates here
        self._def_sup_added = defer.Deferred()
        self._added_count = 0

        self._sub = DatasetSupplementAddedEventSubscriber(process=self._mo)
        def ingest_succeeded(msg):
            self._added_count += 1
            if self._added_count == 5:
                self._def_sup_added.callback(self._added_count)

        self._sub.ondata = ingest_succeeded

        yield self._mo.register_life_cycle_object(self._sub)

        # subscriber so we can just see something is happening
        self._ingest_sub = IngestionProcessingEventSubscriber(process=self._mo)
        def _print_ingest(dat):
            print "INGEST (", dat['content'].additional_data.ingestion_process_id, ") PROCESSING:", dat['content'].additional_data.processing_step

        self._ingest_sub.ondata = _print_ingest

        yield self._mo.register_life_cycle_object(self._ingest_sub)

    @defer.inlineCallbacks
    def _ingest_dataset(self, dsregfile):

        ijr = os.path.join(os.getcwd().rsplit("/", 1)[0], 'ioncore-java-runnables')
        dsreg = OSProcess(binary=os.path.join(ijr, 'dataset_registration'), startdir=ijr, spawnargs=[os.path.join(os.getcwd(), "vandv", "dm16", dsregfile)])
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
    def s1_ingest_5(self):
        """
        1. Start ingestion on five .dsreg files at once
        """

        dlist = defer.DeferredList([self._ingest_dataset('ndbc_sos-44014_airtemp.dsreg'),
                                    self._ingest_dataset('ndbc_sos-44014_currents.dsreg'),
                                    self._ingest_dataset('ndbc_sos-44014_winds.dsreg'),
                                    self._ingest_dataset('ndbc_sos-44013_sea_water_electrical_conductivity.dsreg'),
                                    self._ingest_dataset('cgsn_osu-ismt2_eco-dfl.dsreg')])
        '''
        yield self._ingest_dataset('ndbc_sos-44014_airtemp.dsreg')
        yield self._ingest_dataset('ndbc_sos-44014_currents.dsreg')
        yield self._ingest_dataset('ndbc_sos-44014_winds.dsreg')
        yield self._ingest_dataset('ndbc_sos-44013_sea_water_electrical_conductivity.dsreg')
        yield self._ingest_dataset('cgsn_osu-ismt2_eco-dfl.dsreg')
        '''

        yield dlist

        yield self._def_sup_added
        self._def_sup_added = defer.Deferred()

        self._added_count = 0

        print "datasets", dlist



