#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" This is the CP MediaSilo App daemon, which handles communication
between Cantemo Portal and MediaSilo.
"""

import logging
import requests
import xml.etree.ElementTree as ET
import sqlite3
import time
import os
import codecs
import json
import re
import datetime
import urllib

log = logging.getLogger("main")
vidispine_xml_name_space = "{http://xml.vidispine.com/schema/vidispine}"


class Item():

    """This class holds each item's data."""

    def __init__(self, **kwargs):
        self.portal_item_id = kwargs["portal_item_id"]
        self.quicklink_identifier = kwargs["quicklink_identifier"]
        self.ms_item_id = kwargs["ms_item_id"]
        self.db_id = kwargs["db_id"]
        self.portal_quicklink_uuid = kwargs["portal_quicklink_uuid"]


class QuickLink():

    """This class holds each quicklink's data."""

    def __init__(self, **kwargs):
        self.db_id = kwargs["db_id"]
        self.ms_quicklink_id = kwargs["ms_quicklink_id"]
        self.quicklink_identifier = kwargs["quicklink_identifier"]
        self.quicklink_url = kwargs["quicklink_url"]
        self.expires_at = kwargs["expires_at"]
        self.recipient_mails = kwargs["recipient_mails"]
        self.mail_subject = kwargs["mail_subject"]
        self.mail_body = kwargs["mail_body"]
        self.quicklink_password = kwargs["quicklink_password"]
        self.expiry_date_in_ms = kwargs["expiry_date_in_ms"]


def get_portal_field_value(itemid, field_name, conf):
    vsheaders = {'Content-Type': 'application/xml',
                 'Accept': 'application/xml'}
    vidispine_xml_name_space = "{http://xml.vidispine.com/schema/vidispine}"
    my_xml = requests.get("http://localhost:8080/API/item/%s/metadata;field=%s" %
                          (itemid, field_name),
                          auth=(conf.VS_name, conf.VS_password),
                          headers=vsheaders)
    my_xml = ET.fromstring(my_xml.content)
    try:
        for field in my_xml.find("./%(ns)sitem/%(ns)smetadata/%(ns)stimespan" % {"ns": vidispine_xml_name_space}):
            if field[0].text == field_name:
                field_value = field[1].text
                log.info("Item %s: value of field %s is %s." %
                         (itemid, field_name, field_value))
                if field_value is None:
                    field_value = ""
                return field_value
    except TypeError:
        log.info("Field %s has no value." % field_name)
        return ""


def sync(conf):
    # get values for some variables we need
    configfile = '/opt/cantemo/portal/portal/plugins/CPMediaSiloApp/config.json'
    vsheaders = {'Content-Type': 'application/xml', 'Accept': 'application/xml'}
    cacert_location = "/opt/cantemo/portal/portal/plugins/CPMediaSiloApp/requests/cacert.pem"

    if os.path.isfile(configfile):
        with open(configfile, "r") as config_file:
            try:
                config = json.loads(config_file.read())
            except:
                log.info("Can't read the config file at %s." % configfile)
                return

            # get the MediaSilo hostname, e.g. "moosystems"
            ms_hostname = config["ms_hostname"]

            # get the MediaSilo username, e.g. "aaulich"
            ms_username = config["ms_username"]

            # get the MediaSilo user password.
            ms_password = config["ms_password"]

            # check which MediaSilo project shall be used
            # as default upload location
            default_project = config["default_project"]

    log.info("MediaSilo hostname is '%s'." % ms_hostname)
    log.info("MediaSilo user name is '%s'." % ms_username)
    # log.info("MediaSilo password is '%s'." % ms_password)
    log.info("MediaSilo default project is '%s'." % default_project)

    # send the file to MediaSilo if not available online, yet.

    # Most of the following variables are derived from the variables above
    # this has been the ms url in CPMSA 1.0:
    ms_url = "https://api.mediasilo.com/v3"
    ms_credentials = codecs.encode("%s:%s" % (ms_username, ms_password),
                                   "base64").rstrip()
    msheaders = {'MediaSiloHostContext': ms_hostname,
                 "Authorization": "Basic %s" % ms_credentials,
                 'Content-Type': 'application/json',
                 'Accept': 'application/json'}

    """ Fetch all items from DB, which have no ms_item_id set, yet,
    and upload them to MediaSilo.
    Set ms_item_id in DB and Portal after successful upload. """

    # Let's talk to the database.
    conn = sqlite3.connect(conf.sqlite_db)
    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM items")
        items = cursor.fetchall()

    # create a list which holds all items, which we currently process
    item_objects = []

    for my_item in items:
        log.info("Processing item %s." % repr(my_item))
        portal_item_id = my_item[1]
        quicklink_identifier = my_item[2]
        ms_item_id = my_item[3]
        db_id = my_item[0]
        portal_quicklink_uuid = my_item[4]

        # skip adding this item to item_objects list if it doesn't exist in Portal.
        # In addition delete it from our DB.
        vs_response = requests.get("http://localhost:8080/API/item/%s" % portal_item_id, auth=(
                    conf.VS_name, conf.VS_password), headers=vsheaders).content
        if "ItemDocument" not in vs_response:
            log.info("Portal item %s doesn't exist. Deleting it from our DB." % portal_item_id)
            conn = sqlite3.connect(conf.sqlite_db)
            with conn:
                cursor = conn.cursor()
                # delete item from db
                cursor.execute("""DELETE FROM items WHERE id=?""", (db_id,))
            continue

        # check if the same Portal item has already been stored in the
        # item_objects list. If any of these objects has ms_item_id set, set it
        # for all matching entries in the database.

        # get ms_item_id value from item's Portal metadata:
        ms_item_id_in_portal = get_portal_field_value(portal_item_id, "ms_asset_id", conf)
        if ms_item_id_in_portal not in ["", None, "None", "none"] and ms_item_id != ms_item_id_in_portal:
            ms_item_id = ms_item_id_in_portal
            # update SQLite db with ms_item_id information
            # We store our item in our database
            conn = sqlite3.connect(conf.sqlite_db)
            with conn:
                cursor = conn.cursor()
                cursor.execute("""UPDATE items SET ms_item_id=? WHERE id=?""",
                               (ms_item_id, db_id))

        item = Item(portal_item_id=portal_item_id,
                    quicklink_identifier=quicklink_identifier,
                    ms_item_id=ms_item_id,
                    db_id=db_id,
                    portal_quicklink_uuid=portal_quicklink_uuid)

        item_objects.append(item)

        # Make sure Portal and our db have the same ms_item_id value set
        if ms_item_id is None:
            # make sure we only process items which are available online
            shape_list = requests.get("http://localhost:8080/API/item/%s/shape?url=true" %
                                      portal_item_id, auth=(conf.VS_name, conf.VS_password), headers=vsheaders)
            if shape_list.status_code not in [200, 204]:
                log.info("Can't read media formats of item %s." %
                         portal_item_id)
                continue
            # log.info(shape_list.content)
            shape_list = ET.fromstring(shape_list.content)
            ms_shape_exists = False
            original_shape_exists = False
            for shape in shape_list:
                shape_uri = shape.text

                # we fetch information about our item's shapes
                shape_info = requests.get("%s" % shape_uri, auth=(
                    conf.VS_name, conf.VS_password), headers=vsheaders).content
                shape_info = ET.fromstring(shape_info)

                # we get information about each shape and only deal with the
                # "MediaSilo" shape
                shape_tag = shape_info.find(
                    "./%(ns)stag" % {"ns": vidispine_xml_name_space}).text
                # log.info("Shape tag is %s." % shape_tag)
                if shape_tag == "MediaSilo":
                    ms_shape_exists = True
                if shape_tag == "original":
                    original_shape_exists = True

            log.info("Value of ms_shape_exists is %s." % ms_shape_exists)
            log.info("Value of original_shape_exists is %s." %
                     original_shape_exists)

            # if MediaSilo version not available, yet, try to transcode it
            if ms_shape_exists is True:
                log.info(
                    "Transcoded version for item %s already exists." % portal_item_id)
                pass
            elif original_shape_exists is True:
                log.info("Transcoding MediaSilo file format for Portal item %s." % portal_item_id)
                my_response = requests.post("http://localhost:8080/API/item/%s/transcode?tag=MediaSilo" %
                                            portal_item_id, auth=(conf.VS_name, conf.VS_password), headers=vsheaders)
                try:
                    if my_response.status_code not in [200, 204]:
                        log.info(
                            "Can't trigger transcoding MediaSilo version for item %s." % portal_item_id)
                        log.info("Error message is %s." % my_response.content)
                        continue
                    elif my_response.content not in ["", None, "None"]:
                        # log.info(my_response.content)
                        my_response = ET.fromstring(my_response.content)
                        job_id = my_response.find(
                            "./%(ns)sjobId" % {"ns": vidispine_xml_name_space}).text
                        job_status = my_response.find(
                            "./%(ns)sstatus" % {"ns": vidispine_xml_name_space}).text
                        log.info("Job id is %s, job status is %s." %
                                 (job_id, job_status))
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
            <value>Transcoding</value>
        </field>
    </group>
</group>
</timespan>
</MetadataDocument>""" % portal_quicklink_uuid
                        xml = xml.encode("utf-8")
                        response = requests.put("http://localhost:8080/API/item/%s/metadata/" %
                                                portal_item_id, data=xml, auth=(conf.VS_name, conf.VS_password), headers=vsheaders)
                        if response.status_code not in [200, 204]:
                            log.info("Error message is %s." % response.content)
                            log.info("This is the xml we sent to Portal: %s" % xml)
                            log.info("Skipping item %s." % portal_item_id)
                            continue

                        while job_status not in ["FINISHED", "FAILED_TOTAL"]:
                            time.sleep(10)
                            my_response = requests.get(
                                "http://localhost:8080/API/job/%s" % job_id, auth=(conf.VS_name, conf.VS_password), headers=vsheaders)
                            my_response = ET.fromstring(my_response.content)
                            # log.info(my_response.content)
                            job_status = my_response.find(
                                "./%(ns)sstatus" % {"ns": vidispine_xml_name_space}).text
                            log.info("Status of job %s is %s." %
                                     (job_id, job_status))
                        if job_status == "FAILED_TOTAL":
                            log.info("Could not transcode MediaSilo media format. Skipping item %s." % portal_item_id)
                            continue
                        else:
                            log.info("MediaSilo version for item %s exists, now." % portal_item_id)

                except UnboundLocalError:
                    pass
            else:
                log.info(
                    "No transcoded version and no original media found. Skipping this item.")
                continue

            # get file path of transcoded version
            shape_list = requests.get("http://localhost:8080/API/item/%s/shape?url=true" %
                      portal_item_id, auth=(conf.VS_name, conf.VS_password), headers=vsheaders)
            if shape_list.status_code not in [200, 204]:
                log.info("Can't read media formats of item %s." %
                         portal_item_id)
                continue

            shape_list = ET.fromstring(shape_list.content)
            for shape in shape_list:
                shape_uri = shape.text

                # we fetch information about our item's shapes
                shape_info = requests.get("%s" % shape_uri, auth=(
                    conf.VS_name, conf.VS_password), headers=vsheaders).content
                # log.info(shape_info)
                shape_info = ET.fromstring(shape_info)

                # we get information about each shape and only deal with the
                # "MediaSilo" shape
                shape_tag = shape_info.find(
                    "./%(ns)stag" % {"ns": vidispine_xml_name_space}).text
                # log.info("Shape tag is %s." % shape_tag)
                if shape_tag == "MediaSilo":
                    portal_uri = shape_info.find(
                    "./%(ns)scontainerComponent/%(ns)sfile/%(ns)suri" % {"ns": vidispine_xml_name_space}).text
                    portal_uri = urllib.unquote(re.sub("^file://", "", portal_uri))
            log.info("Local path of MediaSilo version of Portal item is %s." % portal_uri)

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
            <value>Uploading</value>
        </field>
    </group>
</group>
</timespan>
</MetadataDocument>""" % portal_quicklink_uuid
            xml = xml.encode("utf-8")
            response = requests.put("http://localhost:8080/API/item/%s/metadata/" %
                                    portal_item_id, data=xml, auth=(conf.VS_name, conf.VS_password), headers=vsheaders)
            if response.status_code not in [200, 204]:
                log.info("Error message is %s." % response.content)
                log.info("This is the xml we sent to Portal: %s" % xml)
                log.info("Skipping item %s." % portal_item_id)
                continue

            # first we get the id of the default MediaSilo project
            url = "%s/projects" % ms_url
            reply = requests.get(url, verify=cacert_location, headers=msheaders)
            # log.info("Server replied %s." % reply.content)
            content_of_reply = json.loads(reply.content)
            for i in content_of_reply:
                # log.info("Project id: %s - project name: %s" % (i["id"], i["name"]))
                if default_project == i["name"]:
                    default_project_id = i["id"]
            try:
                default_project_id
            except:
                log.info("Our default MediaSilo project doesn't seem to exist. Skipping.")
                continue
            log.info("MediaSilo project id of our default project '%s' is %s." % (default_project, default_project_id))

            # Upload file to MediaSilo and get ms_item_id
            # we start by getting upload info from MediaSilo
            url = "%s/assets/upload" % ms_url
            source_size = os.stat(portal_uri.encode("utf-8")).st_size
            file_name = os.path.basename(portal_uri.encode("utf-8"))
            # file_name = os.path.basename(portal_uri).encode("ascii", "ignore")

            log.info("URL: %s" % url)
            log.info("Source path: %s" % portal_uri)
            log.info("File size: %s bytes" % source_size)

            # only process files smaller than 5GB (MediaSilo upload limit)
            if source_size > 5000000000:
                log.info("File is bigger than 5GB, can't upload it. Skipping item.")

                # delete item from db
                with conn:
                    cursor = conn.cursor()
                    cursor.execute("""DELETE FROM items WHERE id=?""", (db_id,))

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
                <value>File Too Big</value>
            </field>
        </group>
    </group>
    </timespan>
    </MetadataDocument>""" % portal_quicklink_uuid
                xml = xml.encode("utf-8")
                response = requests.put("http://localhost:8080/API/item/%s/metadata/" %
                                        portal_item_id, data=xml, auth=(conf.VS_name, conf.VS_password), headers=vsheaders)
                if response.status_code not in [200, 204]:
                    log.info("Error message is %s." % response.content)
                    log.info("This is the xml we sent to Portal: %s" % xml)
                    log.info("Skipping item %s." % portal_item_id)
                continue

            else:
                log.info("File is smaller than 5GB; start uploading, now.")
            log.info("File name: %s" % file_name)

            def replace_non_ascii(x):
                x = x.replace(" ", "_")
                return ''.join(i if ord(i) < 128 else '_' for i in x)

            payload = json.dumps({"fileName": replace_non_ascii(file_name)})
            reply = requests.post(url, data=payload, verify=cacert_location,
                                  headers=msheaders)
            if reply.status_code not in [200, 204]:
                log.info("Error message is %s." % reply.content)
                # log.info("This is the xml we sent to Portal: %s" % xml)
                log.info("Skipping item %s." % portal_item_id)
                continue

            content_of_reply = json.loads(reply.content)
            assetUrl = content_of_reply["assetUrl"]
            amzDate = content_of_reply["amzDate"]
            amzAcl = content_of_reply["amzAcl"]
            contentType = content_of_reply["contentType"]
            authorization = content_of_reply["authorization"]

            # now create the actual file upload process to a default MediaSilo
            # upload bucket
            upload_headers = {
                "x-amz-date": amzDate,
                "Authorization": authorization,
                "x-amz-acl": amzAcl,
                "Content-Type": contentType
            }

            log.info("Uploading file. That might take some time...")
            try:
                with open(portal_uri.encode("utf-8"), 'rb') as f:
                    requests.put(assetUrl, data=f, verify=cacert_location,
                                 headers=upload_headers)
            except:
                log.info("Could not upload file, will try again later.")
                continue
            if reply.status_code not in [200, 204]:
                log.info("Error message is %s." % reply.content)
                log.info("Skipping item %s." % portal_item_id)
                # os.remove(new_portal_uri.encode("utf-8"))
                continue
            log.info("Successfully uploaded item %s to MediaSilo." % portal_item_id)

            # Move file to our default MediaSilo project
            payload = json.dumps({
                "sourceUrl": assetUrl,
                "projectId": default_project_id
            })

            url = "%s/assets" % ms_url
            reply = requests.post(url, data=payload, verify=cacert_location,
                                  headers=msheaders)
            if reply.status_code not in [200, 204]:
                log.info("Error message is %s." % reply.content)
                log.info("Skipping item %s." % portal_item_id)
                continue
            ms_item_id = json.loads(reply.content)["id"]
            log.info("MediaSilo item id is %s." % ms_item_id)
            # log.info(reply.content)
            # log.info(reply.status_code)

            if ms_item_id in ["", None, "None", "none"]:
                log.info("Haven't found uploaded item on MediaSilo. Skipping.")
                continue
            else:
                item.ms_item_id = ms_item_id
            log.info("MediaSilo asset id of Portal item %s is %s." % (portal_item_id, ms_item_id))

            # update SQLite db with ms_item_id information
            # We store our item in our database
            conn = sqlite3.connect(conf.sqlite_db)
            with conn:
                cursor = conn.cursor()
                cursor.execute("""UPDATE items SET ms_item_id=? WHERE portal_item_id=?""", (ms_item_id, portal_item_id))

            # update item metadata in Portal with ms_item_id information
            xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<MetadataDocument xmlns="http://xml.vidispine.com/schema/vidispine">
<timespan end="+INF" start="-INF">
<group>
    <name>MediaSilo</name>
    <field>
        <name>ms_asset_id</name>
        <value>%s</value>
    </field>
</group>
</timespan>
</MetadataDocument>""" % (ms_item_id)

            xml = xml.encode("utf-8")
            response = requests.put("http://localhost:8080/API/item/%s/metadata/" %
                                    portal_item_id, data=xml, auth=(conf.VS_name, conf.VS_password), headers=vsheaders)
            if response.status_code not in [200, 204]:
                log.info("Error message is %s." % response.content)
                log.info("This is the xml we sent to Portal: %s" % xml)
                log.info("Skipping item %s." % portal_item_id)
                continue
            item.ms_item_id = ms_item_id

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
            <value>Published</value>
        </field>
    </group>
</group>
</timespan>
</MetadataDocument>""" % (portal_quicklink_uuid)
            xml = xml.encode("utf-8")
            response = requests.put("http://localhost:8080/API/item/%s/metadata/" %
                                    portal_item_id, data=xml, auth=(conf.VS_name, conf.VS_password), headers=vsheaders)
            if response.status_code not in [200, 204]:
                log.info("Error message is %s." % response.content)
                log.info("This is the xml we sent to Portal: %s" % xml)
                log.info("Skipping item %s." % portal_item_id)
                continue

    """ Check for all quicklinks without ms_quicklink_id set in DB, for which
    all related items have ms_item_id set.
    Update related items' Portal metadata with quicklink information and
    add ms_quicklink_id value to quicklink in DB. """

    # Let's talk to the database.
    conn = sqlite3.connect(conf.sqlite_db)
    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM quicklinks")
        quick_links = cursor.fetchall()

    # create a list which holds all quicklinks, which we currently process
    quicklinks = []

    for my_quicklink in quick_links:
        log.info("Processing QuickLink %s." % repr(my_quicklink))
        db_id = my_quicklink[0]
        ms_quicklink_id = my_quicklink[1]
        quicklink_identifier = my_quicklink[2]
        quicklink_url = my_quicklink[3]
        expires_at = my_quicklink[4]
        recipient_mails = my_quicklink[5]
        mail_subject = my_quicklink[6]
        mail_body = my_quicklink[7]
        quicklink_password = my_quicklink[8]

        # expiry_date needs to be an epoch timestamp in microseconds
        year = int(expires_at.split("/")[2])
        month = int(expires_at.split("/")[0])
        day = int(expires_at.split("/")[1])

        expiry_date = datetime.date(year=year, month=month, day=day)

        expiry_date_in_ms = expiry_date.strftime('%s') + "000"

        quicklink = QuickLink(db_id=db_id,
                              ms_quicklink_id=ms_quicklink_id,
                              quicklink_identifier=quicklink_identifier,
                              quicklink_url=quicklink_url,
                              expires_at=expires_at,
                              recipient_mails=recipient_mails,
                              mail_subject=mail_subject,
                              mail_body="%s. You need the following password to open this QuickLink: %s" % (mail_body, quicklink_password),
                              quicklink_password=quicklink_password,
                              expiry_date_in_ms=expiry_date_in_ms)
        quicklinks.append(quicklink)

    for my_quicklink in quicklinks:
        log.info("MediaSilo QuickLink id is %s." % my_quicklink.ms_quicklink_id)
        # get all related asset ids
        matching_items = []
        filtered_matching_portal_items = set()
        for item in item_objects:
            if item.quicklink_identifier == my_quicklink.quicklink_identifier:
                matching_items.append(item.ms_item_id)
                filtered_matching_portal_items.add(item.portal_item_id)
        matching_portal_items = []
        for i in filtered_matching_portal_items:
            matching_portal_items.append(i)

        log.info("Related items are %s." % matching_items)

        # remove QuickLink from our DB and stop processing it if no
        # matching Portal items were found.
        if matching_items == []:
            log.info("Removing QuickLink %s from our DB as no related Portal items were found." % my_quicklink)
            conn = sqlite3.connect(conf.sqlite_db)
            with conn:
                cursor = conn.cursor()
                # delete quicklink from db
                cursor.execute("""DELETE FROM quicklinks WHERE id=?""", (my_quicklink.db_id,))
            continue

        if my_quicklink.ms_quicklink_id in [ None, "", "None" ]:
            log.info("Need to create MediaSilo QuickLink for QuickLink %s." % my_quicklink.quicklink_identifier)
            """Generate QuickLink"""
            url = "%s/quicklinks" % ms_url
            json_doc = {"title": "Items shared via Cantemo Portal",
                        "assetIds": matching_items,
                        "configuration": {
                            "id": "",
                            "settings": [
                                {
                                    "key": "audience",
                                    "value": "password"
                                },
                                {
                                    "key": "playback",
                                    "value": "streaming"
                                },
                                {
                                    "key": "allow_download",
                                    "value": "true"
                                },
                                {
                                    "key": "allow_feedback",
                                    "value": "true"
                                },
                                {
                                    "key": "show_metadata",
                                    "value": "true"
                                },
                                {
                                    "key": "notify_email",
                                    "value": "true"
                                },
                                {
                                    "key": "include_directlink",
                                    "value": "false"
                                },
                                {
                                    "key": "password",
                                    "value": quicklink_password
                                }
                            ]
                            },
                        "expires": my_quicklink.expiry_date_in_ms
                        }


            payload = json.dumps(json_doc)

            reply = requests.post(url, data=payload, verify=cacert_location, headers=msheaders)

            if reply.status_code == 500:
                log.info("Can't create QuickLinks in our default MediaSilo project.")
                continue
            reply = reply.content

            try:
                ms_quicklink_id = json.loads(reply)["id"]
            except:
                log.info("This was MediaSilo's reply when we tried to create a QuickLink: %s." % reply)
                log.info("We are skipping QuickLink creation and try again later on.")
                continue
            log.info("Successfully created QuickLink on MediaSilo with id %s." % ms_quicklink_id)
            my_quicklink.ms_quicklink_id = ms_quicklink_id

            # update SQLite db with ms_item_id information
            # We store our item in our database
            log.info("Store QuickLink information in our db.")
            conn = sqlite3.connect(conf.sqlite_db)
            with conn:
                cursor = conn.cursor()
                cursor.execute("""UPDATE quicklinks SET ms_quicklink_id=? WHERE id=?""", (ms_quicklink_id, my_quicklink.db_id))

            # get the quicklink url
            url = "%s/quicklinks/%s" % (ms_url, ms_quicklink_id)
            reply = requests.get(url, verify=cacert_location, headers=msheaders).content
            quicklink_url = json.loads(reply)["url"]

            for portal_item_id in matching_portal_items:
                for item in item_objects:
                    if portal_item_id == item.portal_item_id:

                        # update item metadata in Portal with ms_item_id information
                        # update item's sharing status in Portal metadata
                        xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<MetadataDocument xmlns="http://xml.vidispine.com/schema/vidispine">
<timespan end="+INF" start="-INF">
<group>
    <name>MediaSilo</name>
    <group uuid="%s">
        <name>QuickLink</name>
        <field>
            <name>ms_quick_link</name>
            <value>%s</value>
        </field>
        <field>
            <name>ms_sharing_status</name>
            <value>QuickLink Active</value>
        </field>
    </group>
</group>
</timespan>
</MetadataDocument>""" % (item.portal_quicklink_uuid, quicklink_url)
                        xml = xml.encode("utf-8")
                        log.info("Updating QuickLink information for item %s in Portal." % portal_item_id)
                        response = requests.put("http://localhost:8080/API/item/%s/metadata/" %
                                                portal_item_id, data=xml, auth=(conf.VS_name, conf.VS_password), headers=vsheaders)
                        if response.status_code not in [200, 204]:
                            log.info("Error message is %s." % response.content)
                            log.info("This is the xml we sent to Portal: %s" % xml)
                            log.info("Skipping item %s." % portal_item_id)
                            continue

            """Share QuickLink"""
            mail_recipients = my_quicklink.recipient_mails.split(", ")
            # log.info("Mail body is %s." % my_quicklink.mail_body)
            for mail_recipient in mail_recipients:
                url = "%s/shares" % ms_url
                payload = json.dumps({"targetObjectId": ms_quicklink_id,
                    "emailShare": {
                        "audience": [
                            {
                                "email": mail_recipient,
                            }
                        ],
                        "message": my_quicklink.mail_body,
                        "subject": my_quicklink.mail_subject
                    }
                })
                log.info("Sharing QuickLink information via email with %s." % mail_recipient)
                reply = requests.post(url, data=payload, verify=cacert_location, headers=msheaders)


        else:
            log.info("Already created MediaSilo QuickLink for QuickLink %s." % my_quicklink.quicklink_identifier)

    """ Check for quicklinks with ms_quicklink_id set.
    Fetch comments for all related items from MediaSilo and update
    item metadata in Portal. """

    # get current date as epoch time in milliseconds
    current_date = datetime.datetime.now().date()
    current_date_in_ms = current_date.strftime('%s') + "000"

    # get quicklinks from db, where ms_quicklink_id has been set
    for my_quicklink in quicklinks:

        if my_quicklink.ms_quicklink_id not in [None, "None", ""]:

            # get related items
            matching_item_objects = []
            for item in item_objects:
                if item.quicklink_identifier == my_quicklink.quicklink_identifier:

                    # fetch their comments
                    url = "%s/quicklinks/%s/assets/%s/comments" % (ms_url, my_quicklink.ms_quicklink_id, item.ms_item_id)
                    reply = requests.get(url, verify=cacert_location, headers=msheaders)
                    # log.info("Server replied %s." % reply.content)
                    content_of_reply = json.loads(reply.content)
                    ms_comments = []
                    for my_comment in content_of_reply:
                        comment_content = my_comment["body"]
                        comment_email = my_comment["user"]["email"]
                        comment_id = my_comment["id"]
                        comment_created_epoch = my_comment["dateCreated"]
                        ms_comments.append({"comment_content": comment_content,"comment_email": comment_email, "comment_id": comment_id, "comment_created_epoch": comment_created_epoch})
                    log.info("Comments extracted from MediaSilo for item %s: %s" % (item.portal_item_id, ms_comments))

                    # fetch item's Portal comments related to the current QuickLink
                    log.info("Portal item %s's QuickLink uuid is '%s'." % (item.portal_item_id, item.portal_quicklink_uuid))
                    my_xml = requests.get("http://localhost:8080/API/item/%s/metadata;field=ms_comment_id" %
                                  item.portal_item_id, auth=(conf.VS_name, conf.VS_password), headers=vsheaders)
                    # log.info(my_xml.content)
                    # my_xml = ET.fromstring(my_xml.content)

                    # compare comments
                    for my_comment in ms_comments:
                        if my_comment["comment_id"] in my_xml.content:
                            log.info("Comment with MediaSilo ID %s already exists in Portal item metadata. Skipping." % my_comment["comment_id"])
                        else:
                            # log.info("Current comment: %s" % my_comment)
                            comment_creation_date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(float(my_comment["comment_created_epoch"])))
                            # update item metadata in Portal
                            xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<MetadataDocument xmlns="http://xml.vidispine.com/schema/vidispine">
<timespan end="+INF" start="-INF">
<group>
    <name>MediaSilo</name>
    <group uuid="%s">
        <name>QuickLink</name>
        <group mode="add">
            <name>Comment</name>
            <field>
                <name>ms_comment_date</name>
                <value>%s</value>
            </field>
            <field>
                <name>ms_comment_mail</name>
                <value>%s</value>
            </field>
            <field>
                <name>ms_comment</name>
                <value>%s</value>
            </field>
            <field>
                <name>ms_comment_id</name>
                <value>%s</value>
            </field>
        </group>
    </group>
</group>
</timespan>
</MetadataDocument>""" % (item.portal_quicklink_uuid, comment_creation_date, my_comment["comment_email"], my_comment["comment_content"], my_comment["comment_id"])
                            xml = xml.encode("utf-8")
                            log.info("Updating comment information for item %s in Portal." % item.portal_item_id)
                            # log.info("We send this xml to Portal: %s" % xml)
                            response = requests.put("http://localhost:8080/API/item/%s/metadata/" %
                                                    item.portal_item_id,
                                                    data=xml,
                                                    auth=(conf.VS_name, conf.VS_password),
                                                    headers=vsheaders)
                            if response.status_code not in [200, 204]:
                                log.info("Error message is %s." % response.content)
                                log.info("This is the xml we sent to Portal: %s" % xml)
                                log.info("Skipping item %s." % portal_item_id)
                                continue

            """ Check for expired quicklinks and delete both quicklink and
            related items from database. """
            # log.info("Expiry date: %s." % my_quicklink.expiry_date_in_ms)
            # log.info("Current date: %s." % current_date_in_ms)
            if my_quicklink.expiry_date_in_ms <= current_date_in_ms:
                log.info("Link %s has expired. Removing it from our database." % my_quicklink.quicklink_identifier)
                matching_item_objects = []
                conn = sqlite3.connect(conf.sqlite_db)
                with conn:
                    cursor = conn.cursor()
                    for item in item_objects:
                        if item.quicklink_identifier == my_quicklink.quicklink_identifier:
                            # set item metadata in Portal to link_expired
                            xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<MetadataDocument xmlns="http://xml.vidispine.com/schema/vidispine">
    <timespan end="+INF" start="-INF">
        <group>
            <name>MediaSilo</name>
            <field>
                <name>ms_sharing_status</name>
                <value>QuickLink Expired</value>
            </field>
        </group>
    </timespan>
</MetadataDocument>"""
                            xml = xml.encode("utf-8")
                            response = requests.put("http://localhost:8080/API/item/%s/metadata/" %
                                                    item.portal_item_id, data=xml, auth=(conf.VS_name, conf.VS_password), headers=vsheaders)
                            if response.status_code not in [200, 204]:
                                log.info("Error message is %s." % response.content)
                                log.info("This is the xml we sent to Portal: %s" % xml)
                                log.info("Skipping item %s." % item.portal_item_id)
                                continue
                            # delete item from db
                            cursor.execute("""DELETE FROM items WHERE id=?""", (item.db_id,))
                    # delete quicklink from db
                    cursor.execute("""DELETE FROM quicklinks WHERE id=?""", (my_quicklink.db_id,))
