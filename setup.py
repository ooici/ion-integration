#!/usr/bin/env python

"""
@file setup.py
@author Paul Hubbard
@author Michael Meisinger
@brief setup file for OOI ION Capability Container and Core Modules
@see http://peak.telecommunity.com/DevCenter/setuptools
"""

#from ion.core.ionconst import VERSION

setupdict = {
    'name' : 'ionintegration',
    'version' : '0.0.1', #VERSION,
    'description' : 'OOI ION Integration Tests',
    'url': 'http://www.oceanobservatories.org/spaces/display/CIDev/LCAARCH+Development+Project',
    'download_url' : 'http://ooici.net/packages',
    'license' : 'Apache 2.0',
    'author' : 'Roger Unwin', #of integration test packaging system
    'author_email' : 'raunwin@ucsd.edu',
    'keywords': ['ooici','integration-tests'],
    'classifiers' : [
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Scientific/Engineering'],
}

try:
    from setuptools import setup, find_packages
    setupdict['packages'] = find_packages()

    setupdict['install_requires'] = ['ioncore==0.4.2']

    
    setupdict['include_package_data'] = True
    setup(**setupdict)

except ImportError:
    from distutils.core import setup
    setupdict['packages'] = ['ionint']
    setup(**setupdict)
