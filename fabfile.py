#!/usr/bin/env python

from __future__ import with_statement
from fabric.api import *
from fabric.contrib.console import confirm
import os
import re
import sys

versionTemplates = {
      'python': '''\
#!/usr/bin/env python

# This file is auto-generated. You should not modify by hand.
from _version import Version

# VERSION !!! This is the main version !!!
version = Version('ion', %(major)s, %(minor)s, %(micro)s)
'''
    , 'java-ivy': '<info module="ioncore-java" organisation="net.ooici" revision="%(major)s.%(minor)s.%(micro)s" />'
    , 'java-build': 'version=%(major)s.%(minor)s.%(micro)s'
    , 'git-tag': 'v%(major)s.%(minor)s.%(micro)s'
    , 'git-message': 'Release Version %(major)s.%(minor)s.%(micro)s'
    , 'short': '%(major)s.%(minor)s.%(micro)s'
    , 'setup-py': "version = '%(major)s.%(minor)s.%(micro)s',"
}


# Monkey-patch "open" to honor fabric's current directory
_old_open = open
def open(path, *args, **kwargs):
    return _old_open(os.path.join(env.lcwd, path), *args, **kwargs)

versionRe = re.compile('^(?P<major>[0-9]+)\\.(?P<minor>[0-9]+)\\.(?P<micro>[0-9]+)(?P<pre>[-0-9a-zA-Z]+)?$')
def _validateVersion(v):
    m = versionRe.match(v)
    if not m:
        raise Exception('Version must be in the format <number>.<number>.<number>[<string>]')

    vals = m.groupdict()
    for k in ('major', 'minor', 'micro'): vals[k] = int(vals[k])
    return vals

def _getNextVersion(currentVersionStr):
    cvd = _validateVersion(currentVersionStr)
    nextVersion = '%d.%d.%d' % (cvd['major'], cvd['minor'], cvd['micro'] + 1)

    version = prompt('Please enter the new version (current is "%s"):' % (currentVersionStr),
                     default=nextVersion, validate=_validateVersion)
    return version

def _replaceVersionInFile(filename, matchRe, template, versionCb):
    with open(filename, 'r') as rfile:
        lines = rfile.readlines()

    currentVersionStr = None
    for linenum,line in enumerate(lines):
        m = matchRe.search(line)
        if m:
            vals = m.groupdict()
            indent, currentVersionStr, linesep = vals['indent'], vals['version'], line[-1]
            break

    if currentVersionStr is None:
        abort('Version not found in %s.' % (filename))

    version = versionCb(currentVersionStr)
    nextVersionStr = '%s%s%s' % (indent, template % version, linesep)

    lines[linenum] = nextVersionStr
    with open(filename, 'w') as wfile:
        wfile.writelines(lines)

def _ensureClean():
    with hide('running', 'stdout', 'stderr'):
        branch = local('git name-rev --name-only HEAD', capture=True)
        if branch != 'develop':
            abort('You must be in the "develop" branch (you are in "%s").' % (branch))

        changes = local('git status -s', capture=True)

    clean = (len(changes) == 0)
    if not clean: abort('You have local git modifications, please revert or commit first.')

    local('git pull --rebase')
    local('git fetch --tags')

def _gitTag(version):
    with hide('running', 'stdout', 'stderr'):
        remotes = local('git remote', capture=True).split()
        if len(remotes) == 0:
            abort('You have no configured git remotes.')

    branch = 'develop'
    remote = 'origin' if 'origin' in remotes else remotes[0]
    remote = prompt('Please enter the git remote to use:', default=remote)
    if not remote in remotes:
        abort('"%s" is not a configured remote.' % (remote))

    versionTag = versionTemplates['git-tag'] % version
    versionMsg = versionTemplates['git-message'] % version

    local('git commit -am "%s"' % (versionMsg))
    commit = local('git rev-parse --short HEAD', capture=True)
    local('git tag -af %s -m "%s" %s' % (versionTag, versionMsg, commit))
    local('git push %s %s' % (remote, branch))
    local('git push %s --tags' % (remote))

    print versionTag, versionMsg, commit

    return remote

def _gitForwardMaster(remote, branch='develop'):
    with hide('running', 'stdout', 'stderr'):
        branches = local('git branch', capture=True).split()
        hasMaster = 'master' in branches
        if not hasMaster:
            local('git checkout -b master %s/master' % (remote), capture=True)
            local('git checkout %s' % (branch), capture=True)

    local('git checkout master')
    local('git fetch %s' % (remote))
    local('git merge %s/master' % (remote))
    local('git merge %s' % (branch))
    local('git push %s master' % (remote))

scpUser = None
def _deploy(pkgPattern):
    global scpUser
    if scpUser is None:
        scpUser = os.getlogin()
        scpUser = prompt('Please enter your amoeba login name:', default=scpUser)
    local('scp %s %s@amoeba:/var/www/releases' % (pkgPattern, scpUser))

def python():
    with lcd(os.path.join('..', 'ioncore-python')):
        _ensureClean()

        with hide('running', 'stdout', 'stderr'):
            currentVersionStr = local('python setup.py --version', capture=True)

        nextVersionStr = versionTemplates['python'] % version

        with open(os.path.join('ion', 'core', 'version.py'), 'w') as versionFile:
            versionFile.write(nextVersionStr)

        version = _bumpPythonVersion()
        remote = _gitTag(version)

        local('python setup.py sdist')
        local('chmod -R 775 dist')
        _deploy('dist/*.tar.gz')
        #_gitForwardMaster(remote)

class JavaVersion(object):
    def __init__(self):
        self.version = None
    def __call__(self, currentVersionStr):
        if self.version is None:
            self.version = _getNextVersion(currentVersionStr)
        return self.version

ivyRevisionRe = re.compile('(?P<indent>\s*)<info .* revision="(?P<version>[^"]+)"')
buildRevisionRe = re.compile('(?P<indent>\s*)version=(?P<version>[^\s]+)')
def java():
    with lcd(os.path.join('..', 'ioncore-java')):
        _ensureClean()

        version = JavaVersion()
        _replaceVersionInFile('ivy.xml', ivyRevisionRe, versionTemplates['java-ivy'], version)
        _replaceVersionInFile('build.properties', buildRevisionRe, versionTemplates['java-build'], version)

        remote = _gitTag(version.version)

        local('ant dist')
        local('chmod -R 775 dist/lib')
        _deploy('dist/lib/*.jar')
        #_gitForwardMaster(remote)

setupPyRevisionRe = re.compile("(?P<indent>\s*)version = '(?P<version>[^\s]+)'")
def proto():
    with lcd(os.path.join('..', 'ion-object-definitions')):
        _ensureClean()

        version = JavaVersion()
        _replaceVersionInFile(os.path.join('python', 'setup.py'), setupPyRevisionRe, versionTemplates['setup-py'], version)
        _replaceVersionInFile('ivy.xml', ivyRevisionRe, versionTemplates['java-ivy'], version)
        _replaceVersionInFile('build.properties', buildRevisionRe, versionTemplates['java-build'], version)

        remote = _gitTag(version.version)

        local('ant dist')
        local('chmod -R 775 dist')

        _deploy('dist/lib/*.tar.gz')
        _deploy('dist/lib/*.jar')

