==================================================
Ocean Observatories Initiative Cyberinfrastructure
Integrated Observatory Network (ION)
ioncore-integration - Integration tests for OOICI
==================================================
 
April 2010 - September 2010 (C) UCSD Regents

This project provides a integration testing framework for all the services of the OOI release 1 system with their full
architectural dependencies in Python.

Because these are integration tests they require specific configuration for access to external resources. Developers
are not expected to run all the tests in this package - only the ones relevant to the code you working on.


Contents:
=========
1) Introduction to the tools in ion-integration
2) Setting up your environment
3) Common use cases and tips
4) Creating ITV tests


1) Introduction to the tools in ion-integration
===============================================
The Ion-Integration is a set of integration and system tests that run against our packaged code base.
IonCore-Python, Ion-Object-Definitions and IonCore-Java are imported as dependencies available for integration tests.
Buildout is deploys the packaged depedencies and installs executables in the bin directory including twistd, python,
trial, ipython, cassandra-setup and cassandra-teardown - similar to what is in ioncore-python.

In addition there is a special test runner for the integration package - 'bin/itv'.

$ bin/itv -h
Usage: itv [options]

Options:
  -h, --help            show this help message and exit
  --sysname=SYSNAME     Use this sysname for CCs/trial. If not specified, one
                        is automatically generated.
  --hostname=HOSTNAME   Connect to the broker at this hostname. If not
                        specified, uses localhost.
  --merge               Merge the environment for all integration tests and
                        run them in one shot.
  --no-pause            Do not pause after finding all tests and deps to run.
  --debug               Prints verbose debugging messages.
  --debug-cc            If specified, instead of running trial, drops you into
                        a CC shell after starting apps.
  --wrap-twisted-bin=WRAPBIN
                        Wrap calls to start twisted containers for
                        dependencies in this specified binary. i.e. profiler,
                        valgrind, etc.

The ITV test runner is a tool for running system integration tests. It is capable of starting multiple CC's in a
configurable arrangement. This provides a mechanism for developers to debug problems in a deployment similar to the CEI
environemtn. The ITV test runner can be used to run ITVTestCase classes or to start .itv files which boot particular apps.


ION Integration contains two primary testing directories: itv_tests and trial_tests.

* The trial_tests directory is designed to be run using twisted trial. These are tests which should not be part of the unit test suit
for ioncore-python - generally because they have external dependencies such as cassandra.

* The itv_tests directory is designed to be run using itv executable to launch tests. These are system integration tests. Each app or rel
is started in a separate OS process and more than one instance of any app or rel can be started too. It is up to you to
configure the environment that you want to deploy and test. ITVTestCases are expected to define the apps they depend on
using the app_dependencies class variable in the test case, for example:
    app_dependencies = ["res/apps/echo_example.app"]

It is also possible to use the ITV test runner to launch a system and run tests separately.

For example to launch all 10 boot levels and drop into a shell run:
bin/itv --sysname=mytest_sysname itv_start_files/boot_level_4_local.itv
itv_start_files/boot_level_5.itv itv_start_files/boot_level_6.itv itv_start_files/boot_level_7.itv itv_start_files/boot_level_8.itv
itv_start_files/boot_level_9.itv itv_start_files/boot_level_10.itv

To watch a demonstration of the ion-integration tools see:
https://ooinetwork.webex.com/ooinetwork/ldr.php?AT=pb&SP=MC&rID=29081532&rKey=7e48a71a4b4dead4

2) Setting up your environment
==============================

* Java Development

    Step 1. Install the ivy package manager jar file:  cp ivy.jar ~/.ant/lib

    Step 2. Use ant to install or remove other pacakges:
        ant get-eoi-agents

    You can now run boot_level_10 which start the Java Agent wrapper service.


* Python Developement
    Step 1. Create virtualenv to isolate system site-packages
        mkvirtualenv --no-site-packages --python=/usr/bin/python2.5 <your env>
        workon <your env>

    Step 2. Run 'ant clean' to clean buildout directories, if the virtualenv has previously been created and used.
    
    Step 3. python bootstrap.py (you only need to run this one)
    
    Step 4. Run buildout.  You run this as many times as you switch between buildout configuration files or you want to get the latest dependencies.

        * bin/buildout -c dev-integration.cfg   ==> if you are running against ioncore-python source in your dev environment.
        
        * bin/buildout                          ==> if you are running against latest ioncore-python package.

    If you do bin/buildout you will use developement.cfg which gets the latest release of ioncore-python. If you wish
    to use your development version of ioncore-python then do bin/buildout -c dev-integration.cfg. This assumes that ioncore-python 
    is in the same directory as the ion-integration project.
 
    Step 5.
        a. bin/trial itv_trial
        b. bin/itv itv_trial
            These test will show that the your environment is properly configured - both trial and itv trial are working

    Step 6. You can now configure your environment and run the tests under the two integration test directories:
        a. bin/trial trial_tests/...
        b. bin/itv itv_tests/...

        You will likely need specific entries in your ionlocal.config file to run any given test.


* Clean buildout dependencies (You won't need to do this unless something is really messed up...)
    To completely clean out buildout directories and start fresh:
    ant clean-buildout

3) Common use cases and tips
============================

* Start all 10 boot levels:
bin/itv --sysname=eoitest itv_start_files/boot_level_4_local.itv itv_start_files/boot_level_5.itv
itv_start_files/boot_level_6.itv itv_start_files/boot_level_7.itv itv_start_files/boot_level_8.itv
itv_start_files/boot_level_9.itv itv_start_files/boot_level_10.itv

Once you have started the system using itv files you can run manual tests against the system
** ping the services from the container shell

$ bin/itv itv_start_files/boot_level_4_local.itv
ITV files only specified, no tests: implying --debug-cc
<type 'object'> __builtin__.object
The following app_dependencies will be started:
	res/deploy/bootlevel4_local.rel (via .itv file)
Pausing before starting...
Waiting for container to start: res/deploy/bootlevel4_local.rel
	Lockfile appeared, waiting for container unlock...
	Unlocked!
DEBUG_CC:


    ____                ______                    ____        __  __
   /  _/____  ____     / ____/____  ________     / __ \__  __/ /_/ /_  ____  ____
   / / / __ \/ __ \   / /    / __ \/ ___/ _ \   / /_/ / / / / __/ __ \/ __ \/ __ \
 _/ / / /_/ / / / /  / /___ / /_/ / /  /  __/  / ____/ /_/ / /_/ / / / /_/ / / / /
/___/ \____/_/ /_/   \____/ \____/_/   \___/  /_/    \__, /\__/_/ /_/\____/_/ /_/
                                                    /____/
ION Python Capability Container (version 0.4.22)
[env: /Users/dstuebe/Documents/Dev/virtenvs/ioncore25/lib/python2.5/site-packages]
[container id: dstuebe@dstuebe3.dynamic.ucsd.edu.14936]

><> ping('datastore')
<Deferred #0>
Deferred #0 called back: None
><> ping('datastoreXXX')
<Deferred #1>
><> 2011-06-09 12:16:35.413 [process        :824] WARNING:Process bootstrap RPC conv-id=dstuebe3_dynamic_ucsd_edu_14936.3#2 timed out!
Deferred #1 failed: ''

** run itv tests using regular trial - you have already manually started the system!
You must set the ION_TEST_CASE_SYSNAME os env variable:

$ export ION_TEST_CASE_SYSNAME=mysystem
$ bin/trial itv_tests/boot_level_tests/test_bootlevel4.py
itv_tests.boot_level_tests.test_bootlevel4
  Bootlevel4ReadyTest
    test_all_services ...                                                  [OK]

-------------------------------------------------------------------------------
Ran 1 tests in 1.729s

PASSED (successes=1)


* Using the ioncore-java-runnables directory you can register datasets for ingestion and fire updates!
Add details here on how to get it and install it!


* Turn off that annoying ncml Rsync:
    open the boot_level_8.itv file and change the do-init flag to False.
    ** Commit that change and I will take your little finger!

* To run using cassandra:

You must add entries in your ionlocal.config file -
'ion.core.data.cassandra_schema_script':{
    'cassandra_username':None,
    'cassandra_password':None,
    'sysname':'<Your Sysname>',
    'error_if_existing':False,
},

'ion.core.data.storage_configuration_utility':{
    'storage provider':{'host':'localhost','port':9160}, # Set the host you want to use here!
    'persistent archive':{}
},

'ion.core.data.cassandra_teardown_script':{
    'cassandra_username':None,
    'cassandra_password':None,
    'sysname':'<Your Sysname>',
},


$ bin/cassandra_setup 
    * this script will configure cassandra creating the tables for your deployment

Run the system: bin/itv itv_start_files/boot_level_4.itv ...

$ bin/cassandra_teardown
    * Use this to clean up the tables in cassandra

Be careful using cassandra - it is persistent between runs so it is best to teardown and create a new setup for each test


*) Using the Python profiler 

 To use the python profiler pass in the --profiler argument to the itv script. This will run the profiler and save the
output from each container process as a [service].prof file. Afterwards you can examine the profiling information
using Python's pstats module.

Here is an example on using the
%bin/itv  --profiler=cProfile --sysname=sysname   itv_tests.integration.ais.test_ais.TestAISProcesses 

There is a script in the scripts directory that reads in each of the .prof files and prints out the top 50 functions
that were called the most times, and the top 50 functions that took the most internal time. 

*) Memory leak detection

The ItvTestCase class has a _print_memory_usage method. This prints out the RSS and VSIZE of each of the Capability Container's 
UNIX process. This information is retrieved by calling /bin/ps. This should be done before and after performing an operation to see  
how the operation affects the memory usage of the CC process.  


4) Creating ITV tests

ITV tests run against service which keep going in the background. Changes to the system are not isolated between tests.
This is very different from our unit test framework. Since ION processes are running in seperate containers you can not
get the process object and check state or interact with it - only through messaging!

If existing tests in ioncore-python are written in a way that will work in ITV - then you can import those tests and
use a mixin test class:

Good example:
from ion.integration.ais.test import test_app_integration as app_integration_module
class TestAISProcesses(ItvTestCase, app_integration_module.AppIntegrationTest):

Bad example:
from ion.integration.ais.test.test_app_integration import  AppIntegrationTest
class TestAISProcesses(ItvTestCase, AppIntegrationTest):

But you must import the module under a different name otherwise both the imported test and the new mixin class will run.
This is a quirk of the trial framework - any module imported or in the path with the name test_* will be run.


Change log:
===========
2/1/11 - Added Some tests from ioncore-python that partially fulfil requirements
         UC_R1_18_Command_An_Instrument
         UC_R1_19_Direct_Instrument_Access
         * Note above tests are currently broken due to re-write of DataPubSub
.
