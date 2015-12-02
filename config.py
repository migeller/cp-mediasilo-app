import os
import sys
import requests


def usage():
    print "Usage: install --portal_user=USERNAME --portal_pass=PASSWORD" + "\n"\
        "   where USERNAME is the name of a Portal admin user and" + "\n"\
        "   PASSWORD is the password of the Portal admin user."


class Config:

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
        if result.status_code != 200:
            print "Can't access a local Portal installation using your credentials. Please verify your input and try again."
            sys.exit(1)
        else:
            print "Successfully connected to Portal installation."

        # set some paths
        # This gets the base directory of our script or binary file.
        if getattr(sys, 'frozen', None):
            install_dir = os.path.realpath(
                os.path.dirname(os.path.dirname(__file__)))
            # print "Binary's parent dir is %s." % install_dir
        else:
            install_dir = os.path.realpath(os.path.dirname(__file__))
            print "Script's parent dir is %s." % install_dir
        self.log_file = os.path.join(install_dir, "install.log")

        self.CPMediaSiloApp_source = os.path.join(install_dir,
                                                  "CPMediaSiloApp")
        self.CPMediaSiloApp_target = os.path.join("/opt/cantemo/portal/portal/plugins/",
                                                  "CPMediaSiloApp")
        self.CPMediaSiloApp_config_file = os.path.join("/opt/cantemo/portal/portal/plugins/",
                                                       "CPMediaSiloApp",
                                                       "config.json")
        self.cpmsa_source = os.path.join(install_dir, "cpmsa")
        self.cpmsa_target = os.path.join("/usr/local", "cpmsa")
        self.etc_init_d_source = os.path.join(install_dir, "etc_init_d", "cpmsa")
        self.etc_init_d_target = os.path.join("/etc/init.d", "cpmsa")
        self.sn_source = os.path.join(install_dir, "sn.txt")
        self.sn_target = os.path.join("/usr/local", "cpmsa", "sn.txt")
        self.img_source = os.path.join(install_dir, "img/cpmsa.png")
        self.img_target = os.path.join("/opt/cantemo/portal/portal_media/img",
                                       "cpmsa.png")
