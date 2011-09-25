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
    , 'java-ivy-ioncore-dev': '<info module="ioncore-java" organisation="net.ooici" revision="%(major)s.%(minor)s.%(micro)s-dev" />'
    , 'java-ivy-ioncore': '<info module="ioncore-java" organisation="net.ooici" revision="%(major)s.%(minor)s.%(micro)s" />'
    , 'java-ivy-eoi-agents': '<info module="eoi-agents" organisation="net.ooici" revision="%(major)s.%(minor)s.%(micro)s" />'
    , 'java-ivy-eoi-agents-dev': '<info module="eoi-agents" organisation="net.ooici" revision="%(major)s.%(minor)s.%(micro)s-dev" />'
    , 'java-ivy-proto': '<info module="ionproto" organisation="net.ooici" revision="%(major)s.%(minor)s.%(micro)s" />'
    , 'java-build': 'version=%(major)s.%(minor)s.%(micro)s'
    , 'java-build-dev': 'version=%(major)s.%(minor)s.%(micro)s-dev'
    , 'git-tag': 'v%(major)s.%(minor)s.%(micro)s'
    , 'git-message': 'Release Version %(major)s.%(minor)s.%(micro)s'
    , 'git-proto-greater-message': 'Update ionproto>=%(major)s.%(minor)s.%(micro)s in setup.py'
    , 'short': '%(major)s.%(minor)s.%(micro)s'
    , 'setup-py': "version = '%(major)s.%(minor)s.%(micro)s',"
    , 'setup-py-proto-equal': "'ionproto==%(major)s.%(minor)s.%(micro)s',"
    , 'setup-py-proto-greater': "'ionproto>=%(major)s.%(minor)s.%(micro)s',"
    , 'dev-cfg-equal': 'ionproto=%(major)s.%(minor)s.%(micro)s'
    , 'epu-setup-py': "'version' : '%(major)s.%(minor)s.%(micro)s',"
    , 'epuagent-setup-py': "'version' : '%(major)s.%(minor)s.%(micro)s',"
    , 'epumgmt-setup-py': 'version = "%(major)s.%(minor)s.%(micro)s"'
    , 'ionintegration-setup-py': "version = '%(major)s.%(minor)s.%(micro)s',"
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

    valDict = m.groupdict()
    for k in ('major', 'minor', 'micro'): valDict[k] = int(valDict[k])
    valTuple = (valDict['major'], valDict['minor'], valDict['micro'])
    return valDict, valTuple

def _getNextVersion(currentVersionStr):
    cvd, cvt = _validateVersion(currentVersionStr)
    nextVersion = '%d.%d.%d' % (cvd['major'], cvd['minor'], cvd['micro'] + 1)

    versionD, versionT = prompt('Please enter the new version (current is "%s"):' % (currentVersionStr),
                     default=nextVersion, validate=_validateVersion)

    if versionT <= cvt:
        yesno = prompt('You entered "%s", which is not higher than the current ("%s") and may overwrite a previous release. Are you absolutely SURE? (y/n)' %
                       (versionTemplates['short'] % versionD, currentVersionStr), default='n') 
        if yesno != 'y':
            abort('Invalid version requested, please try again.')

    return versionD


def _getVersionInFile(filename, matchRe):
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
    versionD, versionT = _validateVersion(currentVersionStr)
    return versionD, versionT, currentVersionStr

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

# branchNameRe = re.compile('develop(\\^[0-9]+)?$')
def _ensureClean(default_branch='develop'):
    with hide('running', 'stdout', 'stderr'):
        branch = local('git symbolic-ref HEAD 2>/dev/null || echo unamed branch',
                capture=True).split('/')[-1]
        if default_branch != branch:
            abort('You must be in the %s branch of dir %s. (you are in "%s").' 
                    % (default_branch, local('pwd',capture=True), branch))
        changes = local('git status -s --untracked-files=no', capture=True)

    clean = (len(changes) == 0)
    if not clean: abort('You have local git modifications, please revert or commit first.')

    commitsBehind = int(local('git rev-list ^HEAD | wc -l', capture=True).strip())
    if commitsBehind > 0:
        yesno = prompt('You are %d commits behind HEAD. Are you SURE you want to release this version? (y/n)' % (commitsBehind), default='n')
        if yesno != 'y':
            abort('Local is behind HEAD, please try again.')

    local('git fetch --tags')

def _gitTag(version, branch='develop', cloned=False):
    with hide('running', 'stdout', 'stderr'):
        remotes = local('git remote', capture=True).split()
        if len(remotes) == 0:
            abort('You have no configured git remotes.')

    remote = ('origin' if 'origin' in remotes else
              'ooici' if 'ooici' in remotes else
              'ooici-eoi' if 'ooici-eoi' in remotes else
              remotes[0])
    if not cloned:
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
def _deploy(pkgPattern, recursive=True, subdir=''):
    host = 'amoeba.ucsd.edu'
    remotePath = '/var/www/releases%s' % (subdir)

    global scpUser
    if scpUser is None:
        scpUser = os.getlogin()
        scpUser = prompt('Please enter your amoeba login name:', default=scpUser)

    prefix = ''
    if '*' in pkgPattern:
        prefix = pkgPattern.partition('*')[0]

    recurseFlag = '-r' if recursive else ''
    files = local('find %s' % pkgPattern, capture=True).split()
    relFiles = [file[len(prefix):] for file in files]
    relFileStr = ' '.join(['%s/%s' % (remotePath, file) for file in relFiles])

    # suppress scp -p error status with a superfluous command so we can
    # continue
    local('scp %s %s %s@%s:%s' % (recurseFlag, pkgPattern, scpUser, host, remotePath))
    local('ssh %s@%s chmod 775 %s || exit 0' % (scpUser, host, relFileStr))
    local('ssh %s@%s chgrp teamlead %s || exit 0' % (scpUser, host, relFileStr))
    
def _add_version(project, versionStr):
    print 'Preparing to tar up project directory.'
    local('git clean -f -d')
    local('git rev-parse HEAD > .gitcommit')
    local('echo %s-%s > .projectversion' % (project, versionStr))
    local('rm -rf .git')

def _tar_project_dir(project, versionStr):
    dirtar = '%s_dir-%s.tar.gz' % (project, versionStr)
    local('tar czf %s %s' % (dirtar, project)) 
    print 'Deploying directory tar %s.' % dirtar
    _deploy(dirtar) 

def _releasePython(version_re, versionTemplate, branch):
    currentVersionStr = local('python setup.py --version', capture=True) 
    version = _getNextVersion(currentVersionStr)
    _replaceVersionInFile('setup.py', version_re,
            versionTemplates[versionTemplate], lambda new: version)

    local('rm -rf dist')
    local('python setup.py sdist')
    local('chmod -R 775 dist')
    _deploy('dist/*.tar.gz')
    remote = _gitTag(version, branch=branch, cloned=True)
   
    versionStr = '%d.%d.%d' % (version['major'], version['minor'],
            version['micro'])

    return versionStr

def _releaseDir(branch):
    currentVersionStr = local('cat VERSION.txt', capture=True) 
    version = _getNextVersion(currentVersionStr)
    versionStr = '%d.%d.%d' % (version['major'], version['minor'],
            version['micro'])
    local('echo %s > VERSION.txt' % versionStr)

    remote = _gitTag(version, branch=branch, cloned=True)
   
    return versionStr

def _releaseCEI(project, version_re, versionTemplate, gitUrl,
        default_branch='master', isPython=True):
    local('rm -rf ../tmpfab')
    local('mkdir ../tmpfab')
    local('git clone %s ../tmpfab/%s' % (gitUrl, project))

    with lcd(os.path.join('..', 'tmpfab', project)):
        branch = prompt('Please enter release branch:',
            default=default_branch)

        commit = prompt('Please enter commit to release:',
            default='HEAD')
        local('git checkout %s' % branch)
        local('git reset --hard %s' % commit)
       
        if isPython:
            versionStr = _releasePython(version_re, versionTemplate,
                    branch)
        else:
            versionStr = _releaseDir(branch)

        _add_version(project, versionStr)

    with lcd(os.path.join('..', 'tmpfab')):
        _tar_project_dir(project, versionStr)

    local('rm -rf ../tmpfab')

def _showIntro():
    print '''
-------------------------------------------------------------------------------------------------------------
ION Release Script v1.0
https://confluence.oceanobservatories.org/display/CIDev/Release+Workflow

This is the release script for packaging, tagging, and pushing new versions of various ION components.
This script assumes you are in an "ion-integration" repo clone, which is a sibling of:
"ioncore-python", "ioncore-java", or "ion-object-definitions" (whichever you intend to release).

Prerequisites:
 1) You should not have any local modifications in the repo you wish to release.
 2) You should be on the main line branch, i.e., "develop" or "master"
 branch depending on your project.
 3) You should already be at the exact commit that you want to release as a new version.
 4) You should have already updated your dependent versions in config files and committed (at least locally).
-------------------------------------------------------------------------------------------------------------
'''

setupProtoRe = re.compile("(?P<indent>\s*)'ionproto[><=]=(?P<version>[^']+)'")
devProtoRe = re.compile('(?P<indent>\s*)ionproto[><=]?=(?P<version>.+)')
def python():
    with lcd(os.path.join('..', 'ion-object-definitions', 'python')):
        with hide('running', 'stdout', 'stderr'):
            branch = local('git symbolic-ref HEAD 2>/dev/null || echo unamed branch',
                    capture=True).split('/')[-1]
            if branch != 'develop' :
                abort('You must be in the "develop" branch of dir %s (you are in "%s").' 
                        % (local('pwd', capture=True), branch))
        protoVersion = local('python setup.py --version', capture=True).strip()
        protoVersion = _validateVersion(protoVersion)

    with lcd(os.path.join('..', 'ioncore-python')):

        _showIntro()
        _ensureClean()

        with hide('running', 'stdout', 'stderr'):
            currentVersionStr = local('python setup.py --version', capture=True)

        version = _getNextVersion(currentVersionStr)
        nextVersionStr = versionTemplates['python'] % version

        with open(os.path.join('ion', 'core', 'version.py'), 'w') as versionFile:
            versionFile.write(nextVersionStr)

        # Force the ionproto version before building the package
        _replaceVersionInFile('setup.py', setupProtoRe, versionTemplates['setup-py-proto-equal'], lambda old: protoVersion[0])
        _replaceVersionInFile('development.cfg', devProtoRe, versionTemplates['dev-cfg-equal'], lambda old: protoVersion[0])

        local('rm -rf dist')
        local('python setup.py sdist')
        local('chmod -R 775 dist')
        _deploy('dist/*.tar.gz')

        remote = _gitTag(version)

        # Set the ionproto dependency after version tagging
        _replaceVersionInFile('setup.py', setupProtoRe, versionTemplates['setup-py-proto-greater'], lambda old: protoVersion[0])
        msg = versionTemplates['git-proto-greater-message'] % protoVersion[0]
        local('git commit -am "%s"' % (msg))
        branch = 'develop'
        local('git push %s %s' % (remote, branch))

        #_gitForwardMaster(remote)

def dtdata():
    gitUrl = 'git@github.com:ooici/dt-data.git'

    _releaseCEI('dt-data', 'n/a' , 'n/a', gitUrl, isPython=False)

def launchplans():
    gitUrl = 'git@github.com:ooici/launch-plans.git'

    _releaseCEI('launch-plans', 'n/a' , 'n/a', gitUrl, isPython=False)

def epu():
    gitUrl = 'git@github.com:ooici/epu.git'
    version_re = re.compile("(?P<indent>\s*)'version' : '(?P<version>[^\s]+)'")
    
    _releaseCEI('epu', version_re, 'epu-setup-py', gitUrl)

def epuagent():
    gitUrl = 'git@github.com:ooici/epuagent.git'
    version_re = re.compile("(?P<indent>\s*)'version' : '(?P<version>[^\s]+)'")
   
    _releaseCEI('epuagent', version_re, 'epuagent-setup-py', gitUrl)

def epumgmt():
    gitUrl = 'git://github.com/nimbusproject/epumgmt.git'
    version_re = re.compile('(?P<indent>\s*)version = "(?P<version>[^\s]+)"')
    
    _releaseCEI('epumgmt', version_re, 'epumgmt-setup-py', gitUrl)

def ionintegration():
    gitUrl = 'git@github.com:ooici/ion-integration.git'
    version_re = re.compile("(?P<indent>\s*)version = '(?P<version>[^\s]+)'")

    _releaseCEI('ion-integration', version_re, 'ionintegration-setup-py', gitUrl, default_branch='develop')

# Script to create supercache tar to speed up ion installation during
# launch.
def supercache():
    vm_ip = prompt('Please enter a lv10 worker vm IP:')
    local('ssh root@%s "cd /opt/cache;tar czf my_eggs.tar.gz eggs/;tar czf my_ivy.tar.gz ivy/"' % vm_ip)
    local('rm -rf ../tmpfab')
    local('mkdir ../tmpfab')
    with lcd(os.path.join('..', 'tmpfab')):
        local('scp root@%s:/opt/cache/my*.tar.gz .' % vm_ip)
        local('tar xzf my_eggs.tar.gz')
        local('tar xzf my_ivy.tar.gz')
        # For excluded patterns, rm all the versions except the latest
        for excluded_pattern in ['ionproto-', 'ioncore-']:
            local("for f in `ls eggs| grep %s|sort|sed '$d'`;do rm -rf eggs/$f;done"
                    % excluded_pattern)
        for excluded_pattern in ['ivy/net.ooici/eoi-agents', 'ivy/net.ooici/ionproto',
                'ivy/net.ooici/ioncore-java']:
            local("for f in `ls %s/*.xml|sort|sed '$d'`;do rm $f;done"
                    % excluded_pattern)
            local("for f in `ls %s/*.original|sort|sed '$d'`;do rm $f;done"
                    % excluded_pattern )
            local("for f in `ls %s/*.properties|sort|sed '$d'`;do rm $f;done"
                    % excluded_pattern)
            local("if [ -e %s/jars ];then for f in `ls %s/jars/*|sort|sed '$d'`;do rm $f;done;fi"
                    % (excluded_pattern, excluded_pattern))
            local("if [ -e %s/poms ];then for f in `ls %s/poms/*|sort|sed '$d'`;do rm $f;done;fi"
                    % (excluded_pattern, excluded_pattern))
        local('tar czf supercache.tar.gz ivy/ eggs/')
        global scpUser
        scpUser = os.getlogin()
        scpUser = prompt('Please enter your amoeba login name:', default=scpUser)
        local('ssh %s@amoeba.ucsd.edu "' % scpUser + r'cd /var/www/releases; mv supercache.tar.gz supercache.tar.gz.$(date +%Y%m%d.%H%M)' + '"')
        _deploy('supercache.tar.gz')
    local('rm -rf ../tmpfab')

class JavaVersion(object):
    def __init__(self):
        self.version = None
    def __call__(self, currentVersionStr):
        if self.version is None:
            self.version = _getNextVersion(currentVersionStr)
        return self.version

class JavaNextVersion(object):
    def __init__(self):
        self.version = None
    def __call__(self, currentVersionStr):
        if self.version is None:
            cvd, _ = _validateVersion(currentVersionStr)
            cvd['micro'] = cvd['micro'] + 1
            self.version = cvd
        return self.version

ivyRevisionRe = re.compile('(?P<indent>\s*)<info .* revision="(?P<version>[^"]+)"')
buildRevisionRe = re.compile('(?P<indent>\s*)version=(?P<version>[^\s]+)')
def _getJavaVersion():

    ivyVersionD, ivyVersionT, ivyVersionS = _getVersionInFile('ivy.xml', ivyRevisionRe)
    buildVersionD, buildVersionT, buildVersionS  = _getVersionInFile('build.properties', buildRevisionRe)
    if (ivyVersionT != buildVersionT):
        abort('Versions do not match in ivy.xml and build.properties')
    
    # Chop off suffix
    if buildVersionD['pre'] is not None:
        buildVersionS = ivyVersionS[:-len(buildVersionD['pre'])]
    del buildVersionD['pre']
    
    return buildVersionS, buildVersionD

def _releaseJava(ivyDevVersionTemplate, buildDevVersionTemplate,
        ivyVersionTemplate, buildVersionTemplate, branch):
    
    versionS, versionD = _getJavaVersion()

    # Chop off -dev suffix for release
    _replaceVersionInFile('ivy.xml', ivyRevisionRe,
            versionTemplates[ivyVersionTemplate], lambda new: versionD)
    _replaceVersionInFile('build.properties', buildRevisionRe,
            versionTemplates[buildVersionTemplate], lambda new: versionD)
    
    local('ant ivy-publish-local')
    local('chmod -R 775 .settings/ivy-publish/')
    
    _deploy('.settings/ivy-publish/repository/*', subdir='/maven/repo')
    
    remote =  _gitTag(versionD, branch=branch, cloned=True)
    # Bump version & add -dev suffix
    devVersion = JavaNextVersion()
    devVersion(versionS)
    _replaceVersionInFile('ivy.xml', ivyRevisionRe,
            versionTemplates[ivyDevVersionTemplate], devVersion)
    _replaceVersionInFile('build.properties', buildRevisionRe,
            versionTemplates[buildDevVersionTemplate], devVersion)
    
    devVersion = devVersion.version
    devVersionStr = '%d.%d.%d-dev' % (devVersion['major'], devVersion['minor'],
            devVersion['micro'])
    local('git commit -am "Bump version to %s"' % devVersionStr)
    local('git push %s %s' % (remote, branch))
    
def java():
    gitUrl = 'git@github.com:ooici/ioncore-java.git'
    project = 'ioncore-java'
    default_branch = 'develop'
    
    local('rm -rf ../tmpfab')
    local('mkdir ../tmpfab')
    local('git clone %s ../tmpfab/%s' % (gitUrl, project))
    
    with lcd(os.path.join('..', 'tmpfab', project)):
        branch = prompt('Please enter release branch:',
            default=default_branch)
        commit = prompt('Please enter commit to release:',
            default='HEAD')
        local('git checkout %s' % branch)
        local('git reset --hard %s' % commit)
        
        _releaseJava('java-ivy-ioncore-dev', 'java-build-dev',
                'java-ivy-ioncore', 'java-build', branch)

    local('rm -rf ../tmpfab')

def javadev():
    gitUrl = 'git@github.com:ooici/ioncore-java.git'
    project = 'ioncore-java'
    default_branch = 'develop'
    
    local('rm -rf ../tmpfab')
    local('mkdir ../tmpfab')
    local('git clone %s ../tmpfab/%s' % (gitUrl, project))
    
    with lcd(os.path.join('..', 'tmpfab', project)):
        branch = prompt('Please enter release branch:',
            default=default_branch)
        commit = prompt('Please enter commit to release:',
            default='HEAD')
        local('git checkout %s' % branch)
        local('git reset --hard %s' % commit)
        
        local('ant ivy-publish-local')
        local('chmod -R 775 .settings/ivy-publish/')

        _deploy('.settings/ivy-publish/repository/*', subdir='/maven/repo')

    local('rm -rf ../tmpfab')

def eoiagents():
    gitUrl = 'git@github.com:ooici-eoi/eoi-agents.git'
    project = 'eoi-agents'
    default_branch = 'develop'
    
    local('rm -rf ../tmpfab')
    local('mkdir ../tmpfab')
    local('git clone %s ../tmpfab/%s' % (gitUrl, project))
    
    with lcd(os.path.join('..', 'tmpfab', project)):
        branch = prompt('Please enter release branch:',
            default=default_branch)
        commit = prompt('Please enter commit to release:',
            default='HEAD')
        local('git checkout %s' % branch)
        local('git reset --hard %s' % commit)
        
        _releaseJava('java-ivy-eoi-agents-dev', 'java-build-dev',
                'java-ivy-eoi-agents', 'java-build', branch)

    local('rm -rf ../tmpfab')

setupPyRevisionRe = re.compile("(?P<indent>\s*)version = '(?P<version>[^\s]+)'")
def proto():
    gitUrl = 'git@github.com:ooici/ion-object-definitions.git'
    project = 'ion-object-definitions'
    default_branch = 'develop'
    
    local('rm -rf ../tmpfab')
    local('mkdir ../tmpfab')
    local('git clone %s ../tmpfab/%s' % (gitUrl, project))
    
    with lcd(os.path.join('..', 'tmpfab', project)):
        branch = prompt('Please enter release branch:',
            default=default_branch)
        commit = prompt('Please enter commit to release:',
            default='HEAD')
        local('git checkout %s' % branch)
        local('git reset --hard %s' % commit)
        version = JavaVersion()
        _replaceVersionInFile(os.path.join('python', 'setup.py'), setupPyRevisionRe, versionTemplates['setup-py'], version)
        _replaceVersionInFile('ivy.xml', ivyRevisionRe, versionTemplates['java-ivy-proto'], version)
        _replaceVersionInFile('build.properties', buildRevisionRe, versionTemplates['java-build'], version)

        local('ant ivy-publish-local')
        local('chmod -R 775 dist')
        local('chmod -R 775 .settings/ivy-publish/')

        _deploy('dist/lib/*.tar.gz')
        _deploy('.settings/ivy-publish/repository/*', subdir='/maven/repo')

        remote = _gitTag(version.version)

    local('rm -rf ../tmpfab')
