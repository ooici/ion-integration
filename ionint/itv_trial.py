#!/usr/bin/env python

"""
@file itv_trial
@author Dave Foster <dfoster@asascience.com>
@brief Integration testing with trial.

itv_trial is designed to be a lightweight integration testing framework for
projects based on ION.  The goal is to be able to use the same tests, via trial,
to do integration testing on a CEI bootstrapped system running in a cloud environment,
and a local system where services your tests require are run in separate 
capability containers.

To use, derive your test from ion.test.ItvTestCase and fill in the services class
attribute with a list of apps your test needs. Apps are relative to the current working
directory and typically reside in the res/apps subdir of ioncore-python.

Entries in the "services" class array may be strings pointing to the apps themselves, or
tuples, the first being the string to the app and the second being arguments to pass on
the command line, intended to be used by the services themselves. Some samples:

    # starts a single attribute store app
    services = ["res/apps/attributestore.app"]

    # starts two attribute store apps
    services = [("res/apps/attributestore.app, "id=1")      # id is not used by attributestore but is used
                ("res/apps/attributestore.app, "id=2")]     #   to differentiate the two attributestore
                                                            #   services here.

Example:

    class AttributeStoreTest(ItvTestCase):
        services = ["res/apps/attributestore.app"]  # start these apps prior to testing.

        @defer.inlineCallbacks
        def setUp(self):
            yield self._start_container()

        @defer.inlineCallbacks
        def tearDown(self):
            yield self._stop_container()

        @defer.inlineCallbacks
        def test_set_attr(self):
            asc = AttributeStoreClient()
            yield asc.put("hi", "hellothere")

            res = yield asc.get("hi")
            self.failUnless(res == "hellothere")

        @defer.inlineCallbacks
        def test_set_attr2(self):
            # "hi" is still set here, but only if test_set_attr is run first, be careful
            asc = AttributeStoreClient()
            res = yield asc.get("hi")
            self.failUnless(res == "hellothere")

Important points:
- The sysname parameter is required to get all the services and tests running on the same
  system. itv_trial takes care of this for you, but if you want to deploy these tests vs 
  a CEI spawned environment, you must set the environment variable ION_TEST_CASE_SYSNAME
  to be the same as the sysname the CEI environment was spawned with.
"""

import os, tempfile, signal, time
from twisted.trial.runner import TestLoader
from twisted.trial.unittest import TestSuite
from uuid import uuid4
import subprocess
import optparse

def main():
    # get command line options
    p = optparse.OptionParser()

    p.add_option("--sysname",action="store",dest="sysname")
    p.set_defaults(sysname=str(uuid4()))  # make up a new random sysname
    opts, args = p.parse_args()

    totalsuite = TestLoader().loadByNames(args, True)
    testclasses = set()

    def walksuite(suite, res):
        for x in suite:
            if not isinstance(x, TestSuite):
                res.add(x.__class__)
            else:
                walksuite(x, res)

    walksuite(totalsuite, testclasses)

    print str(totalsuite)

    services = {}

    for x in testclasses:
        #print str(x), "%s.%s" % (cls.__module__, cls.__name__)
        if hasattr(x, 'services'):
            for y in x.services:

                # if not specified as a (appfile, args) tuple, make it one
                if not isinstance(y, tuple):
                    y = (y, None)

                if not services.has_key(y):
                    services[y] = []

                services[y].append(x)

    if len(services) > 0:
        print "The following services will be started:"
        for service in services.keys():
            extra = "(%s)" % ",".join([tc.__name__ for tc in services[service]])
            print "\t", service, extra

        print "Pausing before starting..."
        time.sleep(5)

    ccs = []
    for service in services.keys():

        # build serviceargs to pass to service (should be param=value pairs as strings)
        serviceargs=""
        if service[1]:
            params = service[1]
            if not isinstance(params, list):
                params = [params]
            serviceargs = ",".join(params)

        # build extraargs
        extraargs = "sysname=%s" % opts.sysname
        if len(serviceargs) > 0:
            extraargs += "," + serviceargs

        # temporary log/pid path
        tf = os.path.join(tempfile.gettempdir(), "cc-" + str(uuid4()))

        # build command line
        sargs = ["bin/twistd", "-n", "--pidfile", tf + ".pid", "--logfile", tf + ".log", "cc", "-n", "-a", extraargs, service[0]]

        # set alternate logging conf to just go to stdout
        newenv = os.environ.copy()
        newenv['ION_ALTERNATE_LOGGING_CONF'] = 'res/logging/ionlogging_stdout.conf'

        # spawn container
        po = subprocess.Popen(sargs, env=newenv)

        # add to list of open containers
        ccs.append(po)

    if len(services) > 0:
        print "Waiting for containers to spin up..."
        time.sleep(5)

    # relay signals to trial process we're waiting for
    def handle_signal(signum, frame):
        os.kill(trialpid, signum)

    trialpid = os.fork()
    if trialpid != 0:
        # PARENT PROCESS: this script

        # set new signal handlers to relay signals into trial
        oldterm = signal.signal(signal.SIGTERM, handle_signal)
        #oldkill = signal.signal(signal.SIGKILL, handle_signal)
        oldint  = signal.signal(signal.SIGINT, handle_signal)

        # wait on trial
        try:
            os.wait()
        except OSError:
            pass

        # restore old signal handlers
        signal.signal(signal.SIGTERM, oldterm)
        #signal.signal(signal.SIGKILL, oldkill)
        signal.signal(signal.SIGINT, oldint)
    else:
        # NEW CHILD PROCESS: spawn trial, exec into nothingness
        newenv = os.environ.copy()
        newenv['ION_ALTERNATE_LOGGING_CONF'] = 'res/logging/ionlogging_stdout.conf'
        newenv["ION_TEST_CASE_SYSNAME"] = opts.sysname
        os.execve("bin/trial", ["bin/trial"] + args, newenv)

    def cleanup():
        print "Cleaning up services..."
        for cc in ccs:
            print "\tClosing container with pid:", cc.pid
            os.kill(cc.pid, signal.SIGTERM)

    cleanup()

if __name__ == "__main__":
    main()
