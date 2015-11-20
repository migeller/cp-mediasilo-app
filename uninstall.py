#!/usr/bin/env python
""" This uninstaller uninstalls the CP MediaSilo App."""

import actions
import sys
import os
import shutil
import requests

print "You are removing the CP MediaSilo App."

# Make sure we run as root.
actions.check_if_root()


def usage():
    print "Usage: uninstall --portal_user=USERNAME --portal_pass=PASSWORD" + "\n"\
        "   where USERNAME is the name of a Portal admin user and" + "\n"\
        "   PASSWORD is the password of the Portal admin user."


class config:

    def __init__(self, arg_list):

        # exit if we don't find the right number of arguments
        if len(arg_list) != 2:
            usage()
            sys.exit(2)

        # get the user name.
        self.user = arg_list[0]
        self.user_flag = self.user[0:13]
        self.portal_user = self.user[14:]
        # print self.user_flag
        # print self.portal_user
        if self.user_flag == "--portal_user":
            # print self.portal_user
            pass
        else:
            usage()
            print "You need to set a valid --portal_user!"
            sys.exit(2)

        # get the password.
        self.passw = arg_list[1]
        self.passw_flag = self.passw[0:13]
        self.portal_pass = self.passw[14:]
        # print self.passw_flag
        # print self.portal_pass
        if self.passw_flag == "--portal_pass":
            # print self.portal_pass
            pass
        else:
            usage()
            print "You need to set a valid --portal_pass!"
            sys.exit(2)

        # check if we can connect to Portal using the given user credentials.
        try:
            result = requests.get('http://localhost:8080/API/storage',
                                  auth=(self.portal_user, self.portal_pass))
        except:
            print "Can't access a local Portal installation using your credentials. Please verify your input and try again."
            sys.exit(1)
        if result.status_code not in [200, 204]:
            print "Can't access a local Portal installation using your credentials. Please verify your input and try again."
            sys.exit(1)
        else:
            print "Successfully connected to Portal installation."

# Make sure we have valid arguments sent with our tool.
# Initialize our config.
conf = config(sys.argv[1:])

# stop CP MediaSilo App daemon
print "We are stopping the CP MediaSilo App daemon."
os.system("service cpmsa stop")

# Removing cpmsa autostart
print "We remove cpmsa from init.d."
os.system("chkconfig --del /etc/init.d/cpmsa")

# remove files
# This gets the base directory of our script or binary file.
if getattr(sys, 'frozen', None):
    install_dir = os.path.realpath(os.path.dirname(os.path.dirname(__file__)))
    # print "Binary's parent dir is %s." % app_dir
else:
    install_dir = os.path.realpath(os.path.dirname(__file__))
    # print "Script's parent dir is %s." % app_dir

CPMediaSiloApp_target = os.path.join("/opt/cantemo/portal/portal/plugins/",
                                     "CPMediaSiloApp")
cpmsa_target = os.path.join("/usr/local", "cpmsa")
etc_init_d_target = os.path.join("/etc/init.d", "cpmsa")
img_target = os.path.join("/opt/cantemo/portal/portal_media/img", "cpmsa.png")

print "Removing CP MediaSilo App files."

try:
    shutil.rmtree(CPMediaSiloApp_target, ignore_errors=True)
    print "Successfully removed %s." % CPMediaSiloApp_target
except:
    print "Can't remove %s." % CPMediaSiloApp_target

try:
    shutil.rmtree(cpmsa_target, ignore_errors=True)
    print "Successfully removed %s." % cpmsa_target
except:
    print "Can't remove %s." % cpmsa_target

try:
    os.remove(etc_init_d_target)
    print "Successfully removed %s." % etc_init_d_target
except:
    print "Can't remove %s." % etc_init_d_target

try:
    os.remove(img_target)
    print "Successfully removed %s." % img_target
except:
    print "Can't remove %s." % img_target

# restart Portal
print "Now we restart Portal. This can take a few minutes."
os.system("supervisorctl restart portal")
