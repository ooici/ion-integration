from twisted.internet import defer

#from ion.util import procutils as pu
from ion.vandv.vandvbase import VVBase
import os, os.path, time

from ion.core.object.object_utils import sha1_to_hex
from ion.services.coi.resource_registry.resource_client import ResourceClient
from ion.core.process.process import Process
#from ion.interact.mscweb import MSCWebProcess
from ion.util.os_process import OSProcess
from ion.services.dm.distribution.events import DatasetSupplementAddedEventSubscriber, IngestionProcessingEventSubscriber

import ion.util.ionlog
log = ion.util.ionlog.getLogger(__name__)

class VVDM22(VVBase):
    """
    [Test] The persistent archive services shall support data versioning
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
                                     "itv_start_files/boot_level_10.itv"])

        self._proc = Process(spawnargs={'proc-name':'vvdm22_proc'})
        yield self._proc.spawn()

        self._rc = ResourceClient(proc=self._proc)

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

        """
        self._mscweb = MSCWebProcess()
        yield self._mscweb.spawn()

        # open a browser
        openosp = OSProcess(binary="/usr/bin/open", spawnargs=["http://localhost:9999"])
        yield openosp.spawn()
        """

    @defer.inlineCallbacks
    def s1_ingest_initial_dataset(self):
        """
        1. Instruct one dataset agent to ingest initial dataset
        """

        ijr = os.path.join(os.getcwd().rsplit("/", 1)[0], 'ioncore-java-runnables')
        dsreg = OSProcess(binary=os.path.join(ijr, 'dataset_registration'), startdir=ijr, spawnargs=[os.path.join(os.getcwd(), "vandv", "dm22", "ndbc_sos-44014_winds.dsreg")])
        fin = yield dsreg.spawn()

        # pull out dataset id
        for lines in fin['outlines']:
            for line in lines.split("\n"):
                if "data_set_id: " in line:
                    _, dsid = line.split(" ")
                    self._dataset_id = dsid.strip().strip("\"")
                    break

        yield self._def_sup_added
        self._def_sup_added = defer.Deferred()

        print "We got", self._dataset_id

        yield self._print_cur_ds_state()

    @defer.inlineCallbacks
    def _print_cur_ds_state(self):
        self._dset = yield self._rc.get_instance(self._dataset_id)

        repo = self._dset.Repository

        # get all parent commits, similar to list_parent_commits but not just keys
        commits = []
        branch = repo.get_branch(repo._current_branch.branchkey)
        cref = branch.commitrefs[0]

        while cref:
            commits.append(cref)

            if cref.parentrefs:
                cref = cref.parentrefs[0].commitref
            else:
                cref = None

        # parent -> child ordering
        commits.reverse()

        print '========= Dataset History: =========='
        print '= Dataset ID: %s' % repo.repository_key
        print '= Dataset Branch: %s' % repo.current_branch_key()

        for i, c in enumerate(commits):
            print i+1, "\t", time.strftime("%d %b, %H:%M:%S", time.gmtime(c.date)), "\t", sha1_to_hex(c.MyId), "\t", c.comment

        print '====================================='

    @defer.inlineCallbacks
    def s2_generate_update(self):
        """
        2. Instruct dataset agent to grab any supplemental data
        """
        ijr = os.path.join(os.getcwd().rsplit("/", 1)[0], 'ioncore-java-runnables')
        dsreg = OSProcess(binary=os.path.join(ijr, 'generate_update_event'), startdir=ijr, spawnargs=[self._dataset_id])
        yield dsreg.spawn()

        yield self._def_sup_added
        self._def_sup_added = defer.Deferred()
        yield self._print_cur_ds_state()

    @defer.inlineCallbacks
    def s3_generate_update_2(self):
        """
        3. Instruct dataset agent to grab any supplemental data (again)
        """
        ijr = os.path.join(os.getcwd().rsplit("/", 1)[0], 'ioncore-java-runnables')
        dsreg = OSProcess(binary=os.path.join(ijr, 'generate_update_event'), startdir=ijr, spawnargs=[self._dataset_id])
        yield dsreg.spawn()

        yield self._def_sup_added
        self._def_sup_added = defer.Deferred()
        yield self._print_cur_ds_state()

    @defer.inlineCallbacks
    def s4_show_versions(self):
        """
        4. Show dataset and all available versions of it
        """
        yield self._print_cur_ds_state()

