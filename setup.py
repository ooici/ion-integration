#!/usr/bin/env python

"""
@file setup.py
@author Paul Hubbard
@author Michael Meisinger
@brief setup file for OOI ION Capability Container and Core Modules
@see http://peak.telecommunity.com/DevCenter/setuptools
"""

try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup

setup(
    name = 'ion-integration',
    version = '1.0.0',
    description = 'OOI ION Integration Tests',
    url = 'http://www.oceanobservatories.org/spaces/display/CIDev/LCAARCH+Development+Project',
    download_url = 'http://ooici.net/packages',
    license = 'Apache 2.0',
    author = 'Roger Unwin', 
    author_email = 'raunwin@ucsd.edu',
    keywords = [
        'ooici', 
        'integration-tests'
               ],
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Scientific/Engineering'
                  ],
    packages = find_packages() + ['itv_trial'],
    install_requires = [
        'ioncore<1.1'
                       ],
    include_package_data = True,
    test_suite = "tests"
     )
