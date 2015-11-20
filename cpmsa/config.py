import os
import sys
import requests
import json
import time
import threading


class Config:

    def __init__(self):

        # create pid file and write current pid into that file:
        self.pid_file = os.path.join("/", "var", "run", "cpmsa.pid")
        # self.pid_file = os.path.join("/", "home", "cantemo", "cpaa.pid")
        with open(self.pid_file, "w") as pid_file:
            try:
                pid = str(os.getpid())
                pid_file.write(pid)
            except:
                print "Can't write the PID file at %s. Exiting." % self.pid_file
                sys.exit(1)

        # Read the config file.
        with open("/opt/cantemo/portal/portal/plugins/CPMediaSiloApp/config.json", "r") as config_file:
            try:
                config = json.loads(config_file.read())
            except:
                print "Can't read the config file at /opt/cantemo/portal/portal/plugins/CPMediaSiloApp/config.json. Exiting."
                sys.exit(1)

        # get the Vidispine user name.
        with open("/etc/cantemo/portal/portal.conf", "r") as portal_cfg_file:
            # print portal_cfg_file.readlines()
            for line in portal_cfg_file.readlines():
                if "VIDISPINE_USERNAME" in line:
                    self.VS_name = line.split(" ")[2].rstrip()
                if "VIDISPINE_PASSWORD" in line:
                    self.VS_password = line.split(" ")[2].rstrip()

        # get the MediaSilo hostname:
        self.ms_hostname = config["ms_hostname"]

        # get the MediaSilo username:
        self.ms_username = config["ms_username"]

        # get the MediaSilo password:
        self.ms_password = config["ms_password"]

        # set the port for our daemon.
        self.D_port = 56912

        # check if we can connect to Portal using the given user credentials.
        done = "no"
        my_try = 0
        while done == "no":
                # Automatically try for ten minutes (max) to make sure Portal
                # had enough time to start up after OS reboot
            if my_try == 60:
                print "Can't access a local Portal installation using your credentials. Please verify your input and try again."
                sys.exit(1)
            my_try += 1
            try:
                result = requests.get(
                    'http://localhost:8080/API/storage', auth=(self.VS_name, self.VS_password))
                if result.status_code not in [200, 204]:
                    print "Can't access a local Portal installation using your credentials. Please verify your input and try again."
                    time.sleep(10)
                else:
                    done = "yes"
            except:
                print "Can't access a local Portal installation using your credentials. Please verify your input and try again."
                time.sleep(10)

        # Set up log file.
        # This gets the base directory of our script or binary file.
        app_dir = os.path.join("/", "usr", "local", "cpmsa")
        self.app_dir = app_dir

        self.log_file = os.path.join(app_dir, "daemon.log")

        # Set up SQLite DB path:
        self.sqlite_db = os.path.join("/usr/local/cpmsa", "cpmsa.db")

        # create dictionary to hold all items, which we have sent to MediaSilo
        self.items = {}

        # create dictionary to hold all jobs
        self.jobs = {}

        # create db lock value
        self.sqlite_db_locked = threading.Lock()
