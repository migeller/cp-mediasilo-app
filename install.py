#!/usr/bin/env python
""" This installer installs the CP MediaSilo App and creates all
necessary metadata fields in Portal."""

import config
import md_fields
import requests
import actions
import logging
import logging.handlers
import sys
import shutil
import os
import time

# Make sure we have valid arguments sent with our tool.
# Initialize our config.
conf = config.Config(sys.argv[1:])

print "You are installing the CP MediaSilo App."

# Make sure we run as root.
actions.check_if_root()

# Set up logging.
log = logging.getLogger("installer")
log.setLevel(logging.DEBUG)
handler = logging.handlers.RotatingFileHandler(conf.log_file,
                                               maxBytes=30000000,
                                               backupCount=10)
handler.setLevel(logging.DEBUG)

# Output module name in log when DEBUG mode is active
if log.level == 10:
    fmt = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
else:
    fmt = logging.Formatter('%(asctime)s - %(message)s')
handler.setFormatter(fmt)
log.addHandler(handler)

# create Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter("%(message)s")
console_handler.setFormatter(console_formatter)
log.addHandler(console_handler)

# create CPMediaSiloApp group
my_response = requests.put(
    "http://localhost:8080/API/group/CPMediaSiloApp",
    auth=(conf.portal_user, conf.portal_pass))
if my_response.content == "":
    log.info("Successfully created Portal group 'CPMediaSiloApp'.")
elif my_response.content.startswith("409"):
    log.info("Portal group 'CPMediaSiloApp' already exists. Not touching it.")
else:
    log.info("Couldn't create Portal group 'CPMediaSiloApp'.")
    log.info(my_response.content)

headers = {'Content-Type': 'text/plain'}
description = "Members of this group can share media on MediaSilo."
my_response = requests.put("http://localhost:8080/API/group/CPMediaSiloApp/description",
                           data=description,
                           auth=(conf.portal_user, conf.portal_pass))

log.info("Creating metadata fields in Portal.")
md_fields.create(conf)

# create transcoding profile
headers = {'Content-Type': 'application/xml', 'Accept': 'application/xml'}
xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<TranscodePresetDocument xmlns="http://xml.vidispine.com/schema/vidispine">
  <format>mp4</format>
  <fastStartSetting>
    <requireFastStart>true</requireFastStart>
    <analyzeDuration>true</analyzeDuration>
  </fastStartSetting>
  <audio>
    <codec>aac</codec>
    <bitrate>128000</bitrate>
    <framerate>
      <numerator>1</numerator>
      <denominator>48000</denominator>
    </framerate>
    <channel>0</channel>
    <channel>1</channel>
    <stream>2</stream>
  </audio>
  <video>
    <codec>h264</codec>
    <bitrate>3863000</bitrate>
    <framerate>
      <numerator>1</numerator>
      <denominator>25</denominator>
    </framerate>
    <resolution>
      <width>1280</width>
      <height>720</height>
    </resolution>
    <!-- <maxBFrames>2</maxBFrames> -->
    <pixelFormat>yuv420p</pixelFormat>
    <preset>baseline</preset>
    <setting>
        <key>num_reference_frames</key>
        <value>4</value>
    </setting>
    <setting>
      <key>num_reference_frames</key>
      <value>1</value>
    </setting>
    <setting>
      <key>hrd_maintain</key>
      <value>1</value>
    </setting>
    <setting>
      <key>bit_rate_mode</key>
      <value>H264_CBR</value>
    </setting>
    <setting>
      <key>CABAC</key>
      <value>1</value>
    </setting>
    <setting>
      <key>bit_rate_buffer_size</key>
      <value>750000</value>
    </setting>
  </video>
</TranscodePresetDocument>
"""

my_response = requests.put("http://localhost:8080/API/shape-tag/MediaSilo",
                           data=xml, auth=(conf.portal_user, conf.portal_pass),
                           headers=headers)

# check if CP MediaSilo App config file is already in place. If it is,
# keep config in memory and stop CP MediaSilo App daemon.
conf.CPMediaSiloApp_config = None
if os.path.exists(conf.CPMediaSiloApp_config_file):
    log.info("Stopping current CP MediaSilo App daemon. This takes about 60 seconds.")
    os.system("service cpmsa stop")
    time.sleep(60)
    log.info("Reading existing configuration of the CP MediaSilo App.")
    with open(conf.CPMediaSiloApp_config_file) as config_file:
        conf.CPMediaSiloApp_config = config_file.read()

# Before we copy files to the target, we remove old CP MediaSilo App files
# from Portal
try:
    shutil.rmtree(conf.CPMediaSiloApp_target, ignore_errors=True)
    log.info("Successfully removed %s." % conf.CPMediaSiloApp_target)
except:
    pass

try:
    os.remove(conf.etc_init_d_target)
    log.info("Successfully removed %s." % conf.etc_init_d_target)
except:
    pass

try:
    os.remove(conf.img_target)
    log.info("Successfully removed %s." % conf.img_target)
except:
    pass

try:
    shutil.rmtree(conf.cpmsa_target, ignore_errors=True)
    log.info("Successfully removed %s." % conf.cpmsa_target)
except:
    pass

# Copy files around
try:
    shutil.copytree(conf.CPMediaSiloApp_source,
                    conf.CPMediaSiloApp_target, symlinks=False, ignore=None)
    log.info("Successfully copied %s to its final destination." %
             conf.CPMediaSiloApp_source)
except:
    log.info("Can't copy %s to its final destination." %
             conf.CPMediaSiloApp_source)

# copy cpmsa source files
try:
    shutil.copytree(conf.cpmsa_source,
                    conf.cpmsa_target, symlinks=False, ignore=None)
    log.info("Successfully copied %s into %s." % (conf.cpmsa_source,
                                                  conf.cpmsa_target))
except:
    log.info("Can't copy %s to its final destination." % conf.cpmsa_source)

try:
    shutil.copyfile(conf.etc_init_d_source, conf.etc_init_d_target)
    log.info("Successfully copied %s to its final destination." %
             conf.etc_init_d_source)
except:
    log.info("Can't copy %s to its final destination." %
             conf.etc_init_d_source)

try:
    shutil.copyfile(conf.sn_source, conf.sn_target)
    log.info("Successfully copied %s to its final destination." %
             conf.sn_source)
except:
    log.info("Can't copy %s to its final destination." % conf.sn_source)

try:
    shutil.copyfile(conf.img_source, conf.img_target)
    log.info("Successfully copied %s to its final destination." %
             conf.img_source)
except:
    log.info("Can't copy %s to its final destination." % conf.img_source)

# In case this is an upgrade or reinstall, restore configuration.
if conf.CPMediaSiloApp_config is not None:
    log.info("Restoring existing configuration of the CP MediaSilo App.")
    with open(conf.CPMediaSiloApp_config_file, "w") as config_file:
        config_file.write(conf.CPMediaSiloApp_config)

# change permissions on /etc/init.d/cpmsa
os.system("chmod +x /etc/init.d/cpmsa")

# change permissions on /opt/cantemo/portal/portal/plugins/CPMediaSiloApp
os.system("chmod -R 777 /opt/cantemo/portal/portal/plugins/CPMediaSiloApp")

# set up autostart
log.info("We add cpmsa to /etc/init.d.")
os.system("chkconfig --add /etc/init.d/cpmsa")

# restart Portal
log.info("Now we restart Portal. This can take a few minutes.")
os.system("supervisorctl restart portal")

if conf.CPMediaSiloApp_config is not None:
    log.info("Please verify the CP MediaSilo App configuration in the Portal admin section.")
else:
    log.info("Please configure the CP MediaSilo App in the Portal admin section.")

log.info("Then type 'service cpmsa start' to start the CP MediaSilo App.")
