#!/usr/bin/env python

"""
@file itv_trial
@author Dave Foster <dfoster@asascience.com>
@brief Integration testing with trial.

itv_trial is designed to be a lightweight integration testing framework for
projects based on ION.  The goal is to be able to use the same tests, via trial,
to do integration testing on a CEI bootstrapped system running in a cloud environment,
and a local system where app_dependencies your tests require are run in separate 
capability containers.

This information is superceded by: https://confluence.oceanobservatories.org/display/CIDev/ITV+Trial+tool+and+Integration+Testing



To use, derive your test from ion.test.ItvTestCase and fill in the app_dependencies class
attribute with a list of apps your test needs. Apps are relative to the current working
directory and typically reside in the res/apps subdir of ioncore-python.

Entries in the "app_dependencies" class array may be strings pointing to the apps themselves, or
tuples, the first being the string to the app and the second being arguments to pass on
the command line, intended to be used by the app_dependencies themselves. Some samples:

    # starts a single attribute store app
    app_dependencies = ["res/apps/attributestore.app"]

    # starts two attribute store apps
    app_dependencies = [("res/apps/attributestore.app, "id=1")      # id is not used by attributestore but is used
                ("res/apps/attributestore.app, "id=2")]     #   to differentiate the two attributestore
                                                            #   app_dependencies here.

Example:

    class AttributeStoreTest(ItvTestCase):
        app_dependencies = ["res/apps/attributestore.app"]  # start these apps prior to testing.

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
- The sysname parameter is required to get all the app_dependencies and tests running on the same
  system. itv_trial takes care of this for you, but if you want to deploy these tests vs 
  a CEI spawned environment, you must set the environment variable ION_TEST_CASE_SYSNAME
  to be the same as the sysname the CEI environment was spawned with.
"""

import os, tempfile, signal, time
from twisted.trial.runner import TestLoader, ErrorHolder
from twisted.trial.unittest import TestSuite
from uuid import uuid4
import subprocess
import optparse
import sys
import fcntl
import string

def gen_sysname():
    return str(uuid4())[:6]     # gen uuid, use at most 6 chars

def get_opts():
    """
    Get command line options.
    Sets up option parser, calls gen_sysname to create a new sysname for defaults.
    """
    p = optparse.OptionParser()

    p.add_option("--sysname",         action="store",     dest="sysname",  help="Use this sysname for CCs/trial. If not specified, one is automatically generated.")
    p.add_option("--hostname",        action="store",     dest="hostname", help="Connect to the broker at this hostname. If not specified, uses localhost.")
    p.add_option("--profiler",        action="store",     dest="profiler", help="Use the profiler cprofiler, hotspot, etc for each twistd container process. This saves the profiler output in a file service_prof_output.prof.")
    p.add_option("--merge",           action="store_true",dest="merge",    help="Merge the environment for all integration tests and run them in one shot.")
    p.add_option("--no-pause",        action="store_true",dest="nopause",  help="Do not pause after finding all tests and deps to run.")
    p.add_option("--debug",           action="store_true",dest="debug",    help="Prints verbose debugging messages.")
    p.add_option("--debug-cc",        action="store_true",dest="debug_cc", help="If specified, instead of running trial, drops you into a CC shell after starting apps.")
    p.add_option("--wrap-twisted-bin",action="store",     dest="wrapbin",  help="Wrap calls to start twisted containers for dependencies in this specified binary. i.e. profiler, valgrind, etc.")
    p.add_option("--trial-args",      action="store",     dest="trialargs",help="Arguments passed in to trial, i.e. -u or --coverage")
    p.add_option("--no-busy",         action="store_true",dest="no_busy", help="Set the ION_NO_BUSYLOOP_DETECT env variable so that busy loop detection does not run.")
    p.set_defaults(sysname=gen_sysname(), hostname="localhost", debug=False, debug_cc=False, trialargs=None, no_busy=False )  # make up a new random sysname
    return p.parse_args()

def get_test_classes(testargs, debug=False):
    """
    Gets a set of test classes that will be run.
    Uses the same parsing loader that trial does (which we eventually run).

    @returns    A tuple of all TestCase classes found and all test_ methods found.
    """
    totalsuite = TestLoader().loadByNames(testargs, True)
    all_testclasses = set()     # a set of all TestCase derived classes we find
    all_x = set()               # a set of every single test method in the test suite

    def walksuite(suite, res):
        for x in suite:
            all_x.add(x)
            if isinstance(x, ErrorHolder):
                print "ERROR DETECTED:"
                x.error.printBriefTraceback()

                raise Exception("Trial's test loader found an error, we must abort: %s" % str(x))

            if not isinstance(x, TestSuite):
                if debug:
                    print "Adding to test suites", x.__class__

                res.add(x.__class__)
            else:
                walksuite(x, res)

    walksuite(totalsuite, all_testclasses)

    return (all_testclasses, all_x)

def build_twistd_args(service, serviceargs, pidfile, logfile, lockfile, opts, shell=False):
    """
    Returns an array suitable for spawning a twistd cc container.
    """
    # build extraargs
    extraargs = "sysname=%s" % opts.sysname
    if len(serviceargs) > 0:
        extraargs += "," + serviceargs

    # build command line
    sargs = ["bin/twistd", "-n", "--pidfile", pidfile, "--logfile", logfile] 
       
    if opts.profiler:
        #I assume that service is a string of this format res/apps/service.app
        app_file = service.split(os.sep)[-1]
        service_name = app_file.split(".")[0] 
        sargs +=["--savestats", "--profiler="+ opts.profiler, "--profile", service_name+".prof"]
    
    #Everything before the cc app are arguments to twistd, otherwise they are arguments to cc.
    sargs += ["cc", "-h", opts.hostname]
    
    if lockfile:
        sargs += ["--lockfile", lockfile]
    
    if not shell:
        sargs.append("-n")
    sargs.append("-a")
    sargs.append(extraargs)
    
        
    if service != "":
        sargs.append(service)
    
    # if specified, wrap the twisted container spawn in this exec
    if opts.wrapbin and not shell:
        sargs.insert(0, opts.wrapbin)
    
    return sargs

def main():
    opts, args = get_opts()

    # split args into two groups - probable tests, and .itv eval'able files
    itvfiles = [x for x in args if x.endswith('.itv')]
    testfiles = [x for x in args if x not in itvfiles]

    # parse and load .itvs, merge into one big set
    itvfileapps = []
    for itvfile in itvfiles:
        f = open(itvfile)
        content = f.read()
        f.close()

        try:
            applist = eval(content)
            itvfileapps.extend([x for x in applist if x not in itvfileapps])
        except SyntaxError:
            print "ERROR: Could not parse itv file", itvfile

    if opts.debug and len(itvfileapps) > 0:
        print "Apps to run with all tests (via .itv):", itvfileapps

    # MUST SET THIS ENV VAR before we load tests, otherwise the bootstrap.py will attempt to install a busy loop detection 
    # mechanism which breaks several things here.

    # only set the env if it is not already set
    no_busy_env = os.environ.get('ION_NO_BUSYLOOP_DETECT',None)
    if no_busy_env is None:
        os.environ['ION_NO_BUSYLOOP_DETECT'] = '1'

    all_testclasses, all_x = get_test_classes(testfiles, opts.debug)

    if opts.no_busy is False and no_busy_env is None:
        del os.environ['ION_NO_BUSYLOOP_DETECT']

    # if we have no tests, yet we have itvfiles, that means we need to imply --debug-cc
    if len(testfiles) == 0 and len(itvfileapps) > 0:
        print "ITV files only specified, no tests: implying --debug-cc"
        opts.debug_cc = True

        # we also need to fake that we have a test so the logic below runs
        all_testclasses = [object]

    if opts.debug and len(all_x) == 1:
        print "\n** SINGLE TEST METHOD SPECIFIED **\n"

    if opts.merge:
        # merge all tests into one set
        testset = [all_testclasses]
    else:
        # split out each test on its own
        testset = [[x] for x in all_testclasses]

    # mapping of testclass => result (as a status code, returned by executing trial)
    results = {}

    for testclass in testset:
        app_dependencies = []
        dep_assoc = {}          # associates app deps to test classes
        for x in testclass:
            print str(x), "%s.%s" % (x.__module__, x.__name__)
            if hasattr(x, 'app_dependencies'):
                for y in x.app_dependencies:

                    # add to in order list of app deps
                    if not y in app_dependencies:
                        app_dependencies.append(y)

                    # add association to class (mostly for debugging only)
                    if not dep_assoc.has_key(y):
                        dep_assoc[y] = []

                    dep_assoc[y].append(x)

        # add any and all itv file apps (on the end)
        app_dependencies.extend(itvfileapps)

        if len(app_dependencies) > 0:
            print "The following app_dependencies will be started:"
            for service in app_dependencies:
                if service in itvfileapps:
                    extra = "(via .itv file)"
                else:
                    extra = "(%s)" % ",".join([tc.__name__ for tc in dep_assoc[service]])

                print "\t", service, extra

            if not opts.nopause:
                print "Pausing before starting..."
                time.sleep(5)

        ccs = []
        pid_files = []
        for service in app_dependencies:

            # service - allowed to be a string or a list/tuple iterable, first item must be a string
            if isinstance(service, str):
                servicename = service
                serviceargs = []
            elif hasattr(service, '__iter__'):
                if len(service) == 0 or not isinstance(service[0], str):
                    print "Unknown service specified: list/tuple but first item is not a string?", service
                    continue
                servicename = service[0]
                serviceargs = service[1:]
            else:
                print "Unknown service type specified:", service
                continue

            # build serviceargsstr to pass to service (should be param=value pairs as strings, comma separated, no spaces)
            serviceargsstr=""
            if len(serviceargs) and serviceargs[0] is not None:
                flatparams = []
                for x in serviceargs:
                    if isinstance(x, list):
                        flatparams.extend((string.strip(y) for y in x))
                    else:
                        flatparams.append(string.strip(x))

                serviceargsstr = ",".join(flatparams)

            # build command line
            uniqueid = uuid4()
            basepath = os.path.join(tempfile.gettempdir(), 'cc-%s' % (str(uniqueid)))
            pidfile = '%s.pid' % (basepath)
            logfile = '%s.log' % (basepath)
            lockfile = '%s.lock' % (basepath)
            pid_files.append(pidfile)

            sargs = build_twistd_args(servicename, serviceargsstr, pidfile, logfile, lockfile, opts)

            if opts.debug:
                print sargs

            # set alternate logging conf to just go to stdout
            newenv = os.environ.copy()
            newenv['ION_ALTERNATE_LOGGING_CONF'] = 'res/logging/ionlogging_stdout.conf'

            # spawn container
            po = subprocess.Popen(sargs, env=newenv)

            # add to list of open containers
            ccs.append(po)

            print "Waiting for container to start:", servicename

            # wait for lockfile to appear
            try:
                while not os.path.exists(lockfile):
                    if opts.debug:
                        print "\tWaiting for lockfile", lockfile, "to appear"
                    time.sleep(1)
                else:
                    # ok, lock file is up - wait until os tells us it is unlocked
                    lfh = open(lockfile, 'w')
                    print "\tLockfile appeared, waiting for container unlock..."
                    result = fcntl.lockf(lfh, fcntl.LOCK_EX)
                    print "\tUnlocked!"
                    lfh.close()
                    os.unlink(lockfile)

            except KeyboardInterrupt:
                print "CTRL-C PRESSED, ATTEMPTING TO TERMINATE CCS"

                # must cleanup spawned subprocess(es)!
                for cc in ccs:
                    os.kill(cc.pid, signal.SIGTERM)

                # reraise, should kill program
                raise

            #The containers has started so open the pidfiles
           
            
        # relay signals to trial process we're waiting for
        def handle_signal(signum, frame):
            os.kill(trialpid, signum)

        trialpid = os.fork()
        if trialpid != 0:
            if opts.debug:
                print "TRIAL CHILD PID IS ", trialpid

            # PARENT PROCESS: this script

            # set new signal handlers to relay signals into trial
            oldterm = signal.signal(signal.SIGTERM, handle_signal)
            #oldkill = signal.signal(signal.SIGKILL, handle_signal)
            oldint  = signal.signal(signal.SIGINT, handle_signal)

            # wait on trial
            try:
                cpid, status = os.waitpid(trialpid, 0)

                # STATUS FROM TRIAL:
                # 0     - test OK
                # 256   - test FAIL or ERROR

                results[str(testclass)] = status

                if opts.debug:
                    print "Trial complete for", testclass, " status: ", status

            except OSError:
                pass

            # restore old signal handlers
            signal.signal(signal.SIGTERM, oldterm)
            #signal.signal(signal.SIGKILL, oldkill)
            signal.signal(signal.SIGINT, oldint)
        else:
            # NEW CHILD PROCESS: spawn trial, exec into nothingness
            newenv = os.environ.copy()
            app_pids = []
            for pidfile in pid_files:
                try:
                    f = open(pidfile)
                    pid = f.read(6)
                    f.close()
                    app_pids.append(pid)
                except IOError, ex:
                    print "Problem with the pidfile: %s  errno: %s message: %s" % (pidfile, ex.errno, ex.message)
            newenv["ION_TEST_CASE_PIDS"] = ",".join(app_pids)   
            newenv['ION_ALTERNATE_LOGGING_CONF'] = 'res/logging/ionlogging_stdout.conf'
            newenv["ION_TEST_CASE_SYSNAME"] = opts.sysname
            newenv["ION_TEST_CASE_BROKER_HOST"] = opts.hostname
 
            if not opts.debug_cc:

                # SPECIAL BEHAVIOR FOR SINGLE TEST SPECIFIED
                if len(all_x) == 1:
                    trialargs = args
                
                else:
                    trialargs = ["%s.%s" % (x.__module__, x.__name__) for x in testclass]
                
                #Pass in args to trial
                targs = opts.trialargs
                if targs is not None:
                    trialargs.insert(0, targs)  
                
                os.execve("bin/trial", ["bin/trial"] + trialargs, newenv)
            else:
                # spawn an interactive twistd shell into this system
                print >> sys.stderr, "DEBUG_CC:"

                uniqueid = uuid4()
                basepath = os.path.join(tempfile.gettempdir(), 'cc-%s' % (str(uniqueid)))
                pidfile = '%s-debug-cc.pid' % (basepath)
                logfile = '%s-debug-cc.log' % (basepath)

                sargs = build_twistd_args("", "", pidfile, logfile, None, opts, True)
                os.execve("bin/twistd", sargs, newenv)

        def cleanup():
            print "Cleaning up app_dependencies..."
            for cc in ccs:
                print "\tClosing container with pid:", cc.pid
                os.kill(cc.pid, signal.SIGTERM)

        cleanup()

    exitcode = 0
    resultlen = len(results)
    countfail = 0

    if resultlen > 0:
        print "\n\n++++++++++++++++++++++++++++++++++++++++++++++++++++\n"
        print "ITV TRIAL RESULTS:"

        for testclass, result in results.iteritems():
            classstr = testclass #string.ljust(str(testclass)[:50], 50)
            if result == 0:
                resultstr = "OK"
            elif result == 256:
                # we will at least exit with 1
                exitcode = 1
                # count all the failures
                countfail += 1
                resultstr = "FAIL"
            else:
                resultstr = "UNKNOWN??? (%d)" % result

            print "\t", classstr, "\t", resultstr

        print "\n++++++++++++++++++++++++++++++++++++++++++++++++++++\n\n"

    # if every test class failed, exit with 2
    if countfail == resultlen:
        exitcode = 2

    sys.exit(exitcode)

if __name__ == "__main__":
    main()

