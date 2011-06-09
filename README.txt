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
    
    Step 4. bin/buildout (you run this as many times as you change buildout.cfg and/or its parent files.

    Step 5.
        a. bin/trial itv_trial
        b. bin/itv itv_trial
            These test will show that the your environment is properly configured - both trial and itv trial are working

    Step 6. You can now configure your environment and run the tests under the two integration test directories:
        a. bin/trial trial_tests/...
        b. bin/itv itv_tests/...

        You will likely need specific entries in your ionlocal.config file to run any given test.


* Clean buildout dependencies
    To completely clean out buildout directories and start fresh:
    ant clean-buildout

3) Common use cases and tips
============================

* Start all 10 boot levels:
bin/itv --sysname=eoitest itv_start_files/boot_level_4_local.itv itv_start_files/boot_level_5.itv
itv_start_files/boot_level_6.itv itv_start_files/boot_level_7.itv itv_start_files/boot_level_8.itv
itv_start_files/boot_level_9.itv itv_start_files/boot_level_10.itv

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


*) Using the Cprofiler

 # Please add details

*) Memory leak detection

 # Please add details

Change log:
===========
2/1/11 - Added Some tests from ioncore-python that partially fulfil requirements
         UC_R1_18_Command_An_Instrument
         UC_R1_19_Direct_Instrument_Access
         * Note above tests are currently broken due to re-write of DataPubSub
.
