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

Step 2. python bootstrap.py (you only need to run this one)

Step 3. bin/buildout (you run this as many times as you change buildout.cfg and/or its parent files.


Usage
=====

Step 4. bin/trial ionint

Testing
=======


Build and Packaging using Ant
=============================



Change log:
===========
.
