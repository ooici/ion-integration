#!/usr/bin/env python

"""
@file vandv/dm5.py
@author David Stuebe
@brief DM V&V test #5
"""

from twisted.internet import defer

from ion.util import procutils as pu

from ion.util.os_process import OSProcess

from ion.core import ioninit

class DM5(object):
    """
[Test] Data shall be exportable using the CF Conventions
[Test] The list of external data interfaces shall include the OPeNDAP Data Access Protocol V2

    """
    @defer.inlineCallbacks
    def setup(self):

        binary = 'bin/itv'
        args = ['--sysname=%s' % ioninit.sysname, 'itv_start_files/boot_level_4_local.itv ']
        OSProcess(binary=binary spawnargs=args)

    def s1_broheim(self):
        """
        1. Setup a broheim shindig
        """

        print "3"
        return

    @defer.inlineCallbacks
    def s2_grindig(self):
        """
        2. A grindig is formed
        """

        print "german burger"

        yield pu.asleep(3)
        defer.returnValue(None)

