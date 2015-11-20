#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""This file accepts sharing commands from the Portal UI."""

import SocketServer
import json
import config
import logging
import requests
import xml.etree.ElementTree as ET
import sqlite3
import os
import datetime
import codecs
import uuid
import random
import string
from xml.sax.saxutils import escape

log = logging.getLogger("main")
vidispine_xml_name_space = "{http://xml.vidispine.com/schema/vidispine}"

# Initialize our config.
conf = config.Config()


def get_items(collections):
    # create a list to collect items we need to archive
    headers = {'Content-Type': 'application/xml', 'Accept': 'application/xml'}
    item_list = []
     # get item metadata from Portal
    for collection in collections:
        log.info("Getting items of collection %s." % collection)
        collection_xml = requests.get("http://localhost:8080/API/collection/%s" %
                                      collection, auth=(conf.VS_name, conf.VS_password), headers=headers)
        collection_xml = ET.fromstring(collection_xml.content)
        for field in collection_xml.findall("./%(ns)scontent/%(ns)sid" % {"ns": vidispine_xml_name_space}):
            item_id = field.text
            item_list.append(item_id)
    return item_list


def share_collection(collections,
                     recipient_mail,
                     mail_subject,
                     mail_message,
                     expiry_date):
    item_list = get_items(collections)
    log.info("Items to share: %s" % item_list)
    share(item_list,
          recipient_mail,
          mail_subject,
          mail_message,
          expiry_date)


def share(item_list,
          recipient_mail,
          mail_subject,
          mail_message,
          expiry_date):
    """ Here we trigger sharing of all selected items."""
    headers = {'Content-Type': 'application/xml', 'Accept': 'application/xml'}
    log.info("Check which of the following items we need to share:")
    log.info(item_list)

    # translate mail recipient list into string:
    recipient_mail_string = ""
    for recipient in recipient_mail:
        if recipient_mail_string == "":
            recipient_mail_string += recipient
        else:
            recipient_mail_string = recipient_mail_string + ", " + recipient
    recipient_mail = recipient_mail_string
    log.info("Mail recipients: %s" % recipient_mail)
    log.info("Mail subject: %s" % mail_subject)
    log.info("Mail message: %s" % mail_message)
    log.info("Expiry date: %s" % expiry_date)

    # create a unique identifier for our quicklink:
    quicklink_identifier = str(uuid.uuid4())
    log.info("QickLink identifier: %s" % quicklink_identifier)

    # generate values for quicklink_password
    length = 8
    chars = string.ascii_letters + string.digits
    random.seed = (os.urandom(1024))
    quicklink_password = ''.join(random.choice(chars) for i in range(length))

    # We store our items in our database
    conn = sqlite3.connect(conf.sqlite_db)
    with conn:
        cursor = conn.cursor()
        for item_id in item_list:
            log.info("Portal item id: %s" % item_id)
            query = ("""INSERT INTO items(portal_item_id,
                                          quicklink_identifier) VALUES(?,?)""")
            cursor.execute(query, (item_id, quicklink_identifier))
        query = ("""INSERT INTO quicklinks(recipient_mails,
                                           mail_subject,
                                           mail_body,
                                           quicklink_identifier,
                                           expires_at,
                                           quicklink_password) VALUES(?,?,?,?,?,?)""")
        cursor.execute(query, (recipient_mail,
                               mail_subject,
                               mail_message,
                               quicklink_identifier,
                               expiry_date,
                               quicklink_password))

    # update item metadata in Portal: ms_recipients, ms_mail_subject,
    # ms_mail_message, quicklink_password, ms_shared_on_date, ms_expiry_date

    # generate values for ms_shared_on_date, ms_project

    now = datetime.datetime.now()
    ms_shared_on_date = now.strftime("%m/%d/%Y") # (mm/dd/yyyy)

    # read the config file if it already exists
    configfile = "/opt/cantemo/portal/portal/plugins/CPMediaSiloApp/config.json"
    # log.info("Looking for config file at %s" % configfile)
    try:
        with open(configfile, "r") as config_file:
            try:
                config = json.loads(config_file.read())
            except:
                log.info("Can't read the config file at %s." % configfile)
                return
        # check which MediaSilo project shall be used
        # as default upload location
        ms_project = config["default_project"]
    except:
        log.info("No config file found. Quitting.")
        return

    log.info("QuickLink password: %s." % quicklink_password)
    log.info("Shared on date: %s." % ms_shared_on_date)
    log.info("MediaSilo project: %s." % ms_project)

    for item_id in item_list:
        # log.info(item_id)
        # check if item has already been shared on MediaSilo
        my_xml = requests.get("http://localhost:8080/API/item/%s/metadata" %
                              item_id, auth=(conf.VS_name, conf.VS_password), headers=headers)
        # log.info(my_xml.content)
        my_xml = ET.fromstring(my_xml.content)

        shared_before = False

        try:
            for field in my_xml.find("./%(ns)sitem/%(ns)smetadata/%(ns)stimespan" % {"ns": vidispine_xml_name_space}):
                for child in field.getchildren():
                    try:
                        # log.info("Child tag: %s, child text: %s" % (child.tag, child.text))
                        if child.tag == "{http://xml.vidispine.com/schema/vidispine}name" and child.text == "MediaSilo":
                            shared_before = True
                    except:
                        continue
        except TypeError:
            log.info("Item has not been shared, yet.")

        if shared_before == True:
            log.info("Item has already been shared.")
        else:
            log.info("Item has not been shared, yet.")

        # in case the item has been shared on MediaSilo, check if it has
        # already been uploaded.
        if shared_before == True:
            my_xml = requests.get("http://localhost:8080/API/item/%s/metadata;field=ms_asset_id" %
                                  item_id, auth=(conf.VS_name, conf.VS_password), headers=headers)
            # log.info(my_xml.content)
            my_xml = ET.fromstring(my_xml.content)

            try:
                for field in my_xml.find("./%(ns)sitem/%(ns)smetadata/%(ns)stimespan/%(ns)sgroup" % {"ns": vidispine_xml_name_space}):
                    try:
                        if field[0].text == "ms_asset_id":
                            ms_asset_id = field[1].text
                            if ms_asset_id is None:
                                ms_asset_id = ""
                    except IndexError:
                        continue
                # log.info("Value of field 'ms_asset_id is %s." % ms_asset_id)

            except TypeError:
                log.info("Field 'ms_asset_id' has no value.")
                ms_asset_id = ""

            log.info("Value of field 'ms_asset_id' is '%s'." % ms_asset_id)

        xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<MetadataDocument xmlns="http://xml.vidispine.com/schema/vidispine">
<timespan end="+INF" start="-INF">
<group>
    <name>MediaSilo</name>
    <group mode="add">
        <name>QuickLink</name>
        <field>
           <name>ms_recipients</name>
           <value>%s</value>
        </field>
        <field>
           <name>ms_mail_subject</name>
           <value>%s</value>
        </field>
        <field>
           <name>ms_mail_message</name>
           <value>%s</value>
        </field>
        <field>
           <name>quicklink_password</name>
           <value>%s</value>
        </field>
        <field>
           <name>ms_shared_on_date</name>
           <value>%s</value>
        </field>
        <field>
           <name>ms_sharing_status</name>
           <value>Started Sharing Process</value>
        </field>
        <field>
           <name>ms_expiry_date</name>
           <value>%s</value>
        </field>
    </group>
</group>
</timespan>
</MetadataDocument>""" % (escape(recipient_mail), escape(mail_subject), escape(mail_message),
                          escape(quicklink_password), escape(ms_shared_on_date), escape(expiry_date))

        xml = xml.encode("utf-8")
        # Now that we generated our xml file, we send it to
        # Portal.
        response = requests.put("http://localhost:8080/API/item/%s/metadata/" % item_id, data=xml, auth=(
            conf.VS_name, conf.VS_password), headers=headers)
        if response.status_code not in [200, 204]:
            log.info("Can't update metadata for item %s." % item_id)
            log.info("Error message is %s." % response.content)
            log.info("This is the xml we sent to Portal: %s" % xml)
        else:
            # we need to fetch the portal_quicklink_uuid of the QuickLink we
            # just generated.
            my_response = ET.fromstring(response.content)

            quicklink_dict = {}

            try:
                for group in my_response.findall("./%(ns)sitem/%(ns)smetadata/%(ns)stimespan/%(ns)sgroup/%(ns)sgroup" % {"ns": vidispine_xml_name_space}):
                    portal_quicklink_uuid = group.attrib["uuid"]
                    portal_quicklink_changeid = group.attrib["change"]
                    for field in group.getchildren():
                        if field.tag == "{http://xml.vidispine.com/schema/vidispine}name" and field.text == "QuickLink":
                            quicklink_dict[portal_quicklink_uuid] = portal_quicklink_changeid

            except TypeError:
                log.info("Can't process Portal item %s." % item_id)
                continue

            # First, get all QuickLinks from the MediaSilo group.
            log.info("These are the MediaSilo QuickLinks we found for this item: %s" % repr(quicklink_dict))

            # use the QuickLink with the highest change id
            # for my_quicklink in quicklink_dict:
            highest_changeid = max(quicklink_dict.itervalues())
            log.info("The highest change ID we found is %s." % highest_changeid)

            for portal_quicklink_id, portal_quicklink_changeid in quicklink_dict.iteritems():
                if portal_quicklink_changeid == highest_changeid:
                    portal_quicklink_uuid = portal_quicklink_id
            log.info("We are using the QuickLink with the Portal uuid %s." % portal_quicklink_uuid)

            # update SQLite db with ms_item_id information
            # We store our item in our database
            conn = sqlite3.connect(conf.sqlite_db)
            with conn:
                cursor = conn.cursor()
                cursor.execute("""UPDATE items SET portal_quicklink_uuid=? WHERE quicklink_identifier=? and portal_item_id=?""", (portal_quicklink_uuid, quicklink_identifier, item_id))
                try:
                    if ms_asset_id not in ["", None]:
                        cursor.execute("""UPDATE items SET ms_item_id=? WHERE portal_item_id=?""", (ms_asset_id, item_id))
                except:
                    continue

            if shared_before is True:

                # update item's sharing status in Portal metadata
                xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <MetadataDocument xmlns="http://xml.vidispine.com/schema/vidispine">
    <timespan end="+INF" start="-INF">
    <group>
        <name>MediaSilo</name>
        <group uuid="%s">
            <name>QuickLink</name>
            <field>
                <name>ms_sharing_status</name>
                <value>File Uploaded</value>
            </field>
        </group>
    </group>
    </timespan>
    </MetadataDocument>""" % portal_quicklink_uuid
                response = requests.put("http://localhost:8080/API/item/%s/metadata/" %
                                        item_id, data=xml, auth=(conf.VS_name, conf.VS_password), headers=headers)
                if response.status_code not in [200, 204]:
                    log.info("Error message is %s." % response.content)
                    log.info("This is the xml we sent to Portal: %s" % xml)
                    log.info("Skipping item %s." % item_id)
                    continue


class ThreadedTCPRequestHandler(SocketServer.BaseRequestHandler):

    """This class handles the sharing requests coming in from Portal."""

    def handle(self):
        # Here we fetch info from Portal.
        data = self.request.recv(16384)

        # load our config file as JSON objects
        try:
            input = json.loads(data, strict=False)
        except ValueError as err:
            log.info("Can't interpret received json message. Skipping.")
            log.info("Error: %s" % err)
            response = "JSON error on server. Too many items selected?"
            self.request.sendall(response)
            return

        log.info("Input is %s." % input)

        # get a list of items we need to process
        try:
            items = input["items"]
        except:
            items = []

        # get a list of collections we need to process
        try:
            collections = input["collections"]
        except:
            collections = []

        if items == [] and collections == []:
            response = "You haven't selected any items."
            self.request.sendall(response)
            return

        # get mail recipients
        try:
            recipient_mail_list = input["recipient_mail"].split(",")
            recipient_mail = []
            for recipient in recipient_mail_list:
                recipient_mail.append(recipient.strip(" "))
            log.info("Mail recipients: %s" % recipient_mail)
        except:
            response = "You need to enter one or more comma-separated email addresses."
            log.info("Couldn't extract any mail recipients.")
            self.request.sendall(response)
            return

        # get mail subject
        try:
            mail_subject = input["mail_subject"]
            log.info("Mail subject: %s" % mail_subject)
        except:
            mail_subject = ""

        # get mail message
        try:
            mail_message = input["mail_message"]
            log.info("Mail message: %s" % mail_message)
        except:
            mail_message = ""

        # get expiry date
        try:
            expiry_date = input["expiry_date"]
            log.info("Expiry date: %s" % expiry_date)
        except:
            expiry_date = ""

        # trigger sharing of items
        if items != []:
            response = "Sharing item(s) has started."
            self.request.sendall(response)
            # set a lock before we start
            conf.sqlite_db_locked.acquire()
            share(items,
                  recipient_mail,
                  mail_subject,
                  mail_message,
                  expiry_date)
            # remove sqlite lock
            conf.sqlite_db_locked.release()

        # trigger sharing of  collections
        if collections != []:
            response = "Sharing collection(s) has started."
            self.request.sendall(response)
            # set a lock before we start
            conf.sqlite_db_locked.acquire()
            share_collection(collections,
                             recipient_mail,
                             mail_subject,
                             mail_message,
                             expiry_date)
            # remove sqlite lock
            conf.sqlite_db_locked.release()

        # Tell the client if we don't know what to do
        response = "Don't understand received json message. Skipping."
        self.request.sendall(response)


class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass
