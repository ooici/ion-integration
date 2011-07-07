from twisted.internet import defer

#from ion.util import procutils as pu
from ion.vandv.vandvbase import VVBase
import os, os.path, time

from ion.interact.int_observer import InteractionObserver
from ion.util.os_process import OSProcess
from ion.core.process.process import Process
from ion.services.coi.resource_registry.resource_client import ResourceClient
from ion.services.dm.distribution.events import DatasetSupplementAddedEventSubscriber, IngestionProcessingEventSubscriber

from ion.services.coi.datastore_bootstrap.ion_preload_config import SAMPLE_PROFILE_DATASET_ID

class VVDM12(VVBase):
    """
    [Test] The data catalog services shall be capable of adding metadata attributes
    Implemented using the resource registry and the common data model for science dataset resources.
    Likely basis for DM11 and DM 22 as well!
    """

    @defer.inlineCallbacks
    def setup(self):

        # start full system
        yield self._start_itv(files=["itv_start_files/boot_level_4_local.itv",
                                     ])
        self.proc = Process()
        yield self.proc.spawn()
        self.rc = ResourceClient(proc=self.proc)

    @defer.inlineCallbacks
    def s1_get_dataset(self):
        """
        1. Get an instance of a dataset of a dataset and print the global attributes
        """

        self.dset = yield self.rc.get_instance(SAMPLE_PROFILE_DATASET_ID)
        print self.dset.root_group.attributes.PPrint(name='Attribute')


    def s2_add_dataset_attribute(self):
        """
        2. Add a new global attribute to the dataset and print the attributes again
        """
        group = self.dset.root_group
        group.AddAttribute('NewAttribute', group.DataType.STRING, 'ASA OOICI team kicks ass!')

        print self.dset.root_group.attributes.PPrint(name='Attribute')



    @defer.inlineCallbacks
    def s2_persist_dataset_changes(self):
        """
        2. Push the dataset to the datastore for persistence and print the keys of the new version and the new attributes
        """

        yield self.rc.put_instance(self.dset)
        repo = self.dset.Repository

        print 'Dataset Branch: %s' % repo.current_branch_key
        print 'Dataset ID: %s' % repo.repository_key
