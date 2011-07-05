#!/usr/bin/env python

"""
@file ion/services/dm/inventory/test/test_ncml_generator.py
@author Paul Hubbard
@author Matt Rodriguez
@date 5/2/11
@test ion.services.dm.inventory.ncml_generator Test suite for the NcML code
"""

import os
import tempfile
from uuid import uuid4

from twisted.internet import defer
from ion.core import ioninit
import ion.util.ionlog
from ion.test.iontest import IonTestCase

from ion.services.dm.inventory.ncml_generator import create_ncml, rsync_ncml, do_complete_rsync, clear_ncml_files
from ion.services.dm.inventory import ncml_generator

log = ion.util.ionlog.getLogger(__name__)
CONF = ioninit.config(__name__)

class PSAT(IonTestCase):
    def setUp(self):
        self.old_cmd = ncml_generator.RSYNC_CMD

        self.server_url = 'datactlr@thredds.oceanobservatories.org:/opt/tomcat/ooici_tds_data'
        self.filedir = tempfile.mkdtemp()

    def tearDown(self):
        ncml_generator.RSYNC_CMD = self.old_cmd
        clear_ncml_files(self.filedir)


    def test_premade(self):
        # Borrowed this trick from David Foster. Reference datafile in test dir
        dfile = os.path.join(os.path.dirname(__file__), 'data',
                           '17957467-0650-49c6-b7f5-5321a1cf018e.ncml')

        ref_data = open(dfile).read()

        test_data = create_ncml('17957467-0650-49c6-b7f5-5321a1cf018e').strip()
        
        self.failUnlessEquals(ref_data, test_data)

    @defer.inlineCallbacks
    def test_faked_rsync(self):
        # Switch to a no-op command
        ncml_generator.RSYNC_CMD = 'echo'

        self._make_some_datafiles(5)
        yield rsync_ncml(self.filedir, self.server_url)

    def _make_some_datafiles(self, num_files):
        for idx in range(num_files):
            create_ncml(str(uuid4()), self.filedir)


    @defer.inlineCallbacks
    def test_complete(self):
        # Switch to a no-op command
        ncml_generator.RSYNC_CMD = 'echo'

        yield do_complete_rsync(self.filedir, self.server_url)

    """
    This test is commented out because it requires that there is a unittest account on 
    amoeba that has the id_rsa.pub public key in its ~/.ssh/authorized_keys directory. 
    It will take a little more work to set this up.
    
    @defer.inlineCallbacks
    def test_complete_realkey(self):

        

        self._make_some_datafiles(5)
        server_url = 'unittest@amoeba.ucsd.edu:/opt/ncml'
        print os.listdir(self.filedir)
        yield do_complete_rsync(self.filedir, server_url)
    """