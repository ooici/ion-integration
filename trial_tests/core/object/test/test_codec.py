"""
Created on Jun 8, 2011
@brief Test implementation of the codec class

@file trial_tests/core/object/test/test_codec
@author David Stuebe
@author Matt Rodriguez
@test The object codec test class
"""

import tarfile

from twisted.trial import unittest

from ion.core.object import codec
from ion.core.object import workbench

from ion.core import ioninit
CONF = ioninit.config(__name__)

import ion.util.procutils as pu

class LargeCodecTest(unittest.TestCase):

    def setUp(self):
        wb = workbench.WorkBench('No Process Test')
        self.wb = wb

    def test_copy_large_structure(self):

        filename = CONF.getValue('filename')

        filename = pu.get_ion_path(filename)

        tar = tarfile.open(filename, 'r')
        f = tar.extractfile(tar.next())
        #f = open(filename,'r')

        obj = codec.unpack_structure(f.read())

        f.close()
        tar.close()

        #print obj.PPrint()

        self.wb.put_repository(obj.Repository)

        # Now test copying it!

        repo = self.wb.create_repository()

        # Set a nonsense field to see if we can copy the datastructure!
        repo.root_object = repo.copy_object(obj)

        #print obj.PPrint()


        self.assertNotEqual(repo.root_object._repository, obj._repository)

        repo.commit('My Junk')

        self.assertEqual(repo.root_object, obj)
