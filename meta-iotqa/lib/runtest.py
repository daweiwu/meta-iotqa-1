#!/usr/bin/env python


# Copyright (C) 2015 Intel Corporation
#
# Released under the MIT license (see COPYING.MIT)
# ./runtest.py -b build_data.json testdata.json

import sys
import os
import time
from optparse import OptionParser

try:
    import simplejson as json
except ImportError:
    import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "oeqa")))

from oeqa.oetest import runTests
from oeqa.utils.sshcontrol import SSHControl

# this isn't pretty but we need a fake target object
# for running the tests externally as we don't care
# about deploy/start we only care about the connection methods (run, copy)
class FakeTarget(object):
    def __init__(self, d):
        self.connection = None
        self.ip = None
        self.server_ip = None
        self.datetime = time.strftime('%Y%m%d%H%M%S', time.gmtime())
        self.testdir = d.getVar("TEST_LOG_DIR", True)
        self.pn = d.getVar("PN", True)

    def exportStart(self):
        self.sshlog = os.path.join(self.testdir, "ssh_target_log.%s" % self.datetime)
        sshloglink = os.path.join(self.testdir, "ssh_target_log")
        if os.path.islink(sshloglink):
            os.unlink(sshloglink)
        os.symlink(self.sshlog, sshloglink)
        print("SSH log file: %s" %  self.sshlog)
        self.connection = SSHControl(self.ip, logfile=self.sshlog)

    def run(self, cmd, timeout=None):
        return self.connection.run(cmd, timeout)

    def copy_to(self, localpath, remotepath):
        return self.connection.copy_to(localpath, remotepath)

    def copy_from(self, remotepath, localpath):
        return self.connection.copy_from(remotepath, localpath)

class MyDataDict(dict):
    def getVar(self, key, unused=None):
        return self.get(key, "")

class TestContext(object):
    def __init__(self):
        self.d = None
        self.target = None

def main():

    usage = "usage: %prog [options] <json file>"
    parser = OptionParser(usage=usage)
    parser.add_option("-t", "--target-ip", dest="ip",
            help="The IP address of the target machine. Use this to \
            overwrite the value determined from TEST_TARGET_IP at build time")
    parser.add_option("-s", "--server-ip", dest="server_ip",
            help="The IP address of this machine. Use this to \
            overwrite the value determined from TEST_SERVER_IP at build time.")
    parser.add_option("-d", "--deploy-dir", dest="deploy_dir",
            help="Full path to the package feeds, that this \
            the contents of what used to be DEPLOY_DIR on the build machine. \
            If not specified it will use the value specified in the json if \
            that directory actually exists or it will error out.")
    parser.add_option("-l", "--log-dir", dest="log_dir",
            help="This sets the path for TEST_LOG_DIR. If not specified \
            the current dir is used. This is used for usually creating a \
            ssh log file and a scp test file.")
    parser.add_option("-f", "--test-manifest", dest="tests_list",
            help="The test list file. If not specified \
            the test list come from test description file.")
    parser.add_option("-b", "--build-data", dest="build_data",
            help="The build data file.")
    parser.add_option("-a", "--tag", dest="tag",
            help="The tag to filter test case")

    (options, args) = parser.parse_args()

    tc = TestContext()

    #inject testcase list
    tclist = []
    if options.tests_list:
        with open(options.tests_list, "r") as f:
            tclist = [n.strip() for n in f.readlines()]
    if len(args) == 1:
        with open(args[0], "r") as f:
            tcloaded = json.load(f)
        if options.tag:
            tests = filter(lambda x: options.tag in x["tags"], tcloaded)
            nlist = [ t["testcase"].strip() for t in tests ]
            tclist = filter(lambda x: x in nlist, tclist) if tclist else nlist
    tc.testslist = tclist

    #get build data from file
    if options.build_data:
        with open(options.build_data, "r") as f:
            loaded = json.load(f)
    else:
        loaded = {
              "d": {"DEPLOY_DIR" : "/tmp"},
              "pkgmanifest":[],
              "filesdir": "oeqa/runtime/files",
              "imagefeatures": []
        }

    #inject build datastore
    d = MyDataDict()
    for key in loaded["d"].keys():
        d[key] = loaded["d"][key]

    if options.log_dir:
        d["TEST_LOG_DIR"] = options.log_dir
    else:
        d["TEST_LOG_DIR"] = os.path.abspath(os.path.dirname(__file__))
    if options.deploy_dir:
        d["DEPLOY_DIR"] = options.deploy_dir
    else:
        if not os.path.isdir(d["DEPLOY_DIR"]):
            raise Exception("The path to DEPLOY_DIR does not exists: %s" % d["DEPLOY_DIR"])
    setattr(tc, "d", d)

    #inject build package manifest
    pkgs = [pname.strip() for pname in loaded["pkgmanifest"]]
    setattr(tc, "pkgmanifest", " ".join(pkgs))

    #inject target information
    target = FakeTarget(d)
    target.ip = options.ip if options.ip else "192.168.7.2"
    target.server_ip = options.server_ip if options.server_ip else "192.168.7.1"
    setattr(tc, "target", target)

    #inject others
    for key in loaded.keys():
        if key not in ["testslist", "d", "target", "pkgmanifest"]:
            setattr(tc, key, loaded[key])

    print tc.testslist
    target.exportStart()
    runTests(tc)

    return 0

if __name__ == "__main__":
    try:
        ret = main()
    except Exception:
        ret = 1
        import traceback
        traceback.print_exc(5)
    sys.exit(ret)
