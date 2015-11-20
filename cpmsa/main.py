#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""This is the main file running the CP MediaSilo App."""

from request_handler import *
import config
import share
import sys
import logging
import logging.handlers
import os
import sqlite3
import threading
import signal
import errno
import time
import socket

CPMSA_VERSION = "1.0.4"

"""Initialize our app"""

# Initialize our config.
conf = config.Config()

# Set up logging.
log = logging.getLogger("main")
log.setLevel(logging.DEBUG)
handler = logging.handlers.RotatingFileHandler(
    conf.log_file, maxBytes=30000000, backupCount=10)
handler.setLevel(logging.DEBUG)

# Output module name in log when DEBUG mode is active
fmt = logging.Formatter('%(asctime)s - %(message)s')
handler.setFormatter(fmt)
log.addHandler(handler)

# Spit out version number
log.info("We are running CP MediaSilo App version %s." % CPMSA_VERSION)

# make sure our CPMSA database exists.
if os.path.isfile(conf.sqlite_db):
    log.info("CPMSA database file already exists.")
    # load all items and jobs from the database file
    conf.items = {}
    conf.jobs = {}
else:
    # if the db doesn't exist, create it

    # set a lock before we start
    conf.sqlite_db_locked.acquire()

    log.info("Creating CPMSA database.")
    conn = sqlite3.connect(conf.sqlite_db)
    with conn:
        cursor = conn.cursor()
        cursor.execute("""CREATE TABLE quicklinks(
                          id INTEGER PRIMARY KEY AUTOINCREMENT,
                          ms_quicklink_id TEXT UNIQUE,
                          quicklink_identifier TEXT UNIQUE,
                          quicklink_url TEXT UNIQUE,
                          expires_at TEXT,
                          recipient_mails TEXT,
                          mail_subject TEXT,
                          mail_body TEXT,
                          quicklink_password TEXT
                          );
                      """)
        cursor.execute("""CREATE TABLE items(
                          id INTEGER PRIMARY KEY AUTOINCREMENT,
                          portal_item_id TEXT,
                          quicklink_identifier TEXT,
                          ms_item_id TEXT,
                          portal_quicklink_uuid TEXT
                          );
                      """)
        cursor.execute("""CREATE INDEX Idx1 ON items(portal_item_id,
                          quicklink_identifier,
                          ms_item_id,
                          portal_quicklink_uuid);
                      """)
    # remove sqlite lock
    conf.sqlite_db_locked.release()


"""Server section"""

# First set IP address and port to which our server listens.
# While the IP address will always be localhost, the port
# may vary.
# Port 0 means to select an arbitrary unused port.
HOST, PORT = "localhost", conf.D_port

# Now we define the server
try:
    server = ThreadedTCPServer((HOST, PORT), ThreadedTCPRequestHandler)
except socket.error as e:
    if e.errno == errno.EADDRINUSE:
        print "Address already in use. The CP MediaSilo App daemon is most probably already running."
    else:
        print "Error code is: %s" % error_code
    sys.exit(1)
server.allow_reuse_address = True
ip, port = server.server_address
log.info("Server port is %s." % port)
# Exit the server thread when the main thread terminates
server.daemon = True

# Start a thread with the server -- that thread will then start one
# more thread for each request
server_thread = threading.Thread(target=server.serve_forever)
# Exit the server thread when the main thread terminates
# server_thread.daemon = True
server_thread.start()


"""Transfer items to MediaSilo, create QuickLinks and send out invitations."""

check_sync_thread = True
# make sure that the following code runs once a minute


def sync():
    while check_sync_thread == True:
        # set a lock before we start
        conf.sqlite_db_locked.acquire()
        share.sync(conf)
        # remove sqlite lock
        conf.sqlite_db_locked.release()
        time.sleep(60)
    log.info("CPMSA daemon successfully stopped.")

sync_thread = threading.Thread(target=sync)
sync_thread.start()


""" Set up signal handler to exit gracefully if asked for."""


def signal_handler(signal, frame):
    global check_sync_thread
    # Say goodbye
    log.info("Preparing clean daemon shutdown. This can take a while.")
    # shut down the TCP server
    server.shutdown()
    server.server_close()
    # shut down the sync_thread:
    check_sync_thread = False
    sync_thread.join()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
log.info('Press Ctrl+C to stop this application.')
# wait for kill -s INT 60843 or Control-C to finish
signal.pause()
