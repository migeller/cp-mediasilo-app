import os
import sys


def check_if_root():
    if not os.geteuid() == 0:
        print "This installer requires root permissions. Please try again using sudo or run as root."
        sys.exit(1)