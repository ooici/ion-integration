from twisted.internet import defer

#from ion.util import procutils as pu
from ion.vandv.vandvbase import VVBase
import os, os.path, time

from ion.core.object.object_utils import sha1_to_hex, create_type_identifier
from ion.services.coi.resource_registry.resource_client import ResourceClient
from ion.core.process.process import Process
#from ion.interact.mscweb import MSCWebProcess
from ion.util.os_process import OSProcess, OSProcessError
from ion.services.dm.distribution.events import DatasetSupplementAddedEventSubscriber, IngestionProcessingEventSubscriber

import ion.util.ionlog
log = ion.util.ionlog.getLogger(__name__)

CDM_BOUNDED_ARRAY_TYPE = create_type_identifier(object_id=10021, version=1)

class VVDM15(VVBase):
    """
    [Test] The data catalog services shall permanently associate metadata with all cataloged data
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

        self._proc = Process(spawnargs={'proc-name':'vvdm15_proc'})
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
        dsreg = OSProcess(binary=os.path.join(ijr, 'dataset_registration'), startdir=ijr, spawnargs=[os.path.join(os.getcwd(), "vandv", "dm15", "ndbc_sos-44014_winds.dsreg")])
        fin = yield dsreg.spawn()

        # pull out dataset id
        for lines in fin['outlines']:
            for line in lines.split("\n"):
                if "data_set_id: " in line:
                    _, dsid = line.split(" ")
                    self._dataset_id = dsid.strip().strip("\"")
                    break

        print 'Waiting for supplement added event:'
        yield self._def_sup_added
        self._def_sup_added = defer.Deferred()

        print "We got", self._dataset_id

        yield self._print_cur_ds_state()

    @defer.inlineCallbacks
    def _print_cur_ds_state(self):
        self._dset = yield self._rc.get_instance(self._dataset_id, excluded_types=[CDM_BOUNDED_ARRAY_TYPE])

        repo = self._dset.Repository

        # get all parent commits, similar to list_parent_commits but not just keys
        commits = []
        branch = repo._current_branch
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
            links = []
            try:
                for var in c.objectroot.resource_object.root_group.variables:
                    links.extend(var.content.bounded_arrays.GetLinks())

                # get em
                yield repo.fetch_links(links)

                for var in c.objectroot.resource_object.root_group.variables:
                    outlines = []

                    for ba in var.content.bounded_arrays:
                        outlines.append("%s%s\t%s" % (" "*40, sha1_to_hex(ba.MyId)[0:6] + "...", " ".join(["[%s+%s]" % (x.origin, x.size) for x in ba.bounds])))

                    varname = " "*4 + str(var.name)
                    if len(outlines) > 1:
                        varname += " (%d)" % len(outlines)

                    outlines[0] = varname + outlines[0][len(varname):]

                    print "\n".join(outlines)

            except:# Exception, ex:
                pass
                #print ex
                #print dir(var)
                #print "made it here"
                #links.extend(var.content.bounded_arrays.GetLinks())


            # display em


        print '====================================='

    @defer.inlineCallbacks
    def s2_generate_update(self):
        """
        2. Instruct dataset agent to grab any supplemental data
        """
        ijr = os.path.join(os.getcwd().rsplit("/", 1)[0], 'ioncore-java-runnables')
        dsreg = OSProcess(binary=os.path.join(ijr, 'generate_update_event'), startdir=ijr, spawnargs=[self._dataset_id])
        yield dsreg.spawn()

        print 'Waiting for supplement added event:'
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

        print 'Waiting for supplement added event:'
        yield self._def_sup_added
        self._def_sup_added = defer.Deferred()
        yield self._print_cur_ds_state()

    @defer.inlineCallbacks
    def s4_teardown_system(self):
        """
        4. Tell entire system to shutdown.
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
        except OSProcessError:#, ex:
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
    def s5_restart_system(self):
        """
        5. Restart the system
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
    def s6_show_versions(self):
        """
        6. Show dataset and all available versions of it
        """
        yield self._print_cur_ds_state()

