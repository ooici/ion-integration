==================================================
Ocean Observatories Initiative Cyberinfrastructure
Integrated Observatory Network (ION)
ioncore-integration - Integration tests for OOICI
==================================================
 
April 2010 - September 2010 (C) UCSD Regents

This project provides a integration testing framework for all 
the services of the OOI release 1 system with their full 
architectural dependencies in Python.

For more information, please see:

Dependencies
============
    Step 1. Create virtualenv to isolate system site-packages
        mkvirtualenv --no-site-packages --python=/usr/bin/python2.5 buildout
        workon buildout

    Step 2. Run 'ant clean' to clean buildout directories, if the virtualenv has previously been created and used.
    
    Step 3. python bootstrap.py (you only need to run this one)
    
    Step 4. bin/buildout (you run this as many times as you change buildout.cfg and/or its parent files.


Develop
=====

    Step 5. bin/trial ionint

    If you want to re-run step 5, it is reccomended to rerun step 2 (ant clean) between runs of trial.


Testing
=======


Build and Packaging using Ant
=============================



Change log:
===========
2/1/11 - Added Some tests from ioncore-python that partially fulfil requirements
         UC_R1_18_Command_An_Instrument
         UC_R1_19_Direct_Instrument_Access
         * Note above tests are currently broken due to re-write of DataPubSub
.
