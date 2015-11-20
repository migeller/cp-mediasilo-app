import requests
import logging
import sys

log = logging.getLogger("installer")


def create(conf):
    """
    This function creates a metadata group named "MediaSilo" in Portal.
    At the same time it creates all necessary metadata fields in that group,
    and makes them accessible for members of the group CPMediaSiloApp.
    """

    # We create an XML file, which we can send to Portal to create necessary
    # md fields
    xml = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    xml = xml + '<MetadataFieldGroupDocument xmlns="http://xml.vidispine.com/schema/vidispine">\n'

    xml = xml + '<name>MediaSilo</name>\n'
    xml = xml + '<schema min="0" max="1" name="MediaSilo" />\n'
    xml = xml + '<data>\n'
    xml = xml + '<key>extradata</key>\n'
    xml = xml + '<value>{"field_order": [ "ms_asset_id", "QuickLink" ] }</value>\n'
    xml = xml + '</data>\n'

    xml = xml + '<field>\n'
    xml = xml + '<name>ms_asset_id</name>\n'
    xml = xml + '<type>string</type>\n'
    xml = xml + '<stringRestriction>\n'
    xml = xml + '<maxLength>1024</maxLength>\n'
    xml = xml + '</stringRestriction>\n'
    xml = xml + '<data>\n'
    xml = xml + '<key>extradata</key>\n'
    xml = xml + '<value>{"name": "MediaSilo Asset ID", "type": "string"}</value>\n'
    xml = xml + '</data>\n'
    xml = xml + '</field>\n'

    """xml = xml + '<name>QuickLink</name>\n'
    xml = xml + '<schema min="0" max="-1" name="QuickLink" />\n'
    xml = xml + '<data>\n'
    xml = xml + '<key>extradata</key>\n'
    xml = xml + '<value>{"field_order": [ "ms_sharing_status", "ms_quick_link", "quicklink_password", "ms_shared_on_date", "ms_expiry_date", "ms_recipients", "ms_mail_subject", "ms_mail_message", "Comment" ] }</value>\n'
    xml = xml + '</data>\n'"""

    xml = xml + '<group>\n'
    xml = xml + '<name>QuickLink</name>\n'
    xml = xml + '<data>\n'
    xml = xml + '<key>extradata</key>\n'
    xml = xml + '<value>{"field_order": [ "ms_sharing_status", "ms_quick_link", "quicklink_password", "ms_shared_on_date", "ms_expiry_date", "ms_recipients", "ms_mail_subject", "ms_mail_message", "Comment" ] }</value>\n'
    xml = xml + '</data>\n'

    xml = xml + '<field>\n'
    xml = xml + '<name>ms_quick_link</name>\n'
    xml = xml + '<type>string</type>\n'
    xml = xml + '<stringRestriction>\n'
    xml = xml + '<maxLength>1024</maxLength>\n'
    xml = xml + '</stringRestriction>\n'
    xml = xml + '<data>\n'
    xml = xml + '<key>extradata</key>\n'
    xml = xml + '<value>{"name": "QuickLink URL", "type": "string"}</value>\n'
    xml = xml + '</data>\n'
    xml = xml + '</field>\n'

    xml = xml + '<field>\n'
    xml = xml + '<name>quicklink_password</name>\n'
    xml = xml + '<type>string</type>\n'
    xml = xml + '<stringRestriction>\n'
    xml = xml + '<maxLength>64</maxLength>\n'
    xml = xml + '</stringRestriction>\n'
    xml = xml + '<data>\n'
    xml = xml + '<key>extradata</key>\n'
    xml = xml + '<value>{"name": "QuickLink Password", "type": "string"}</value>\n'
    xml = xml + '</data>\n'
    xml = xml + '</field>\n'

    xml = xml + '<field>\n'
    xml = xml + '<name>ms_shared_on_date</name>\n'
    xml = xml + '<type>string</type>\n'
    xml = xml + '<data>\n'
    xml = xml + '<key>extradata</key>\n'
    xml = xml + '<value>{"name": "Shared on Date", "type": "string"}</value>\n'
    xml = xml + '</data>\n'
    xml = xml + '</field>\n'

    xml = xml + '<field>\n'
    xml = xml + '<name>ms_expiry_date</name>\n'
    xml = xml + '<type>string</type>\n'
    xml = xml + '<data>\n'
    xml = xml + '<key>extradata</key>\n'
    xml = xml + '<value>{"name": "Expiry Date", "type": "string"}</value>\n'
    xml = xml + '</data>\n'
    xml = xml + '</field>\n'

    xml = xml + '<field>\n'
    xml = xml + '<name>ms_recipients</name>\n'
    xml = xml + '<type>string</type>\n'
    xml = xml + '<stringRestriction>\n'
    xml = xml + '<maxLength>1024</maxLength>\n'
    xml = xml + '</stringRestriction>\n'
    xml = xml + '<data>\n'
    xml = xml + '<key>extradata</key>\n'
    xml = xml + '<value>{"name": "Mail Recipients", "type": "string"}</value>\n'
    xml = xml + '</data>\n'
    xml = xml + '</field>\n'

    xml = xml + '<field>\n'
    xml = xml + '<name>ms_mail_subject</name>\n'
    xml = xml + '<type>string</type>\n'
    xml = xml + '<stringRestriction>\n'
    xml = xml + '<maxLength>1024</maxLength>\n'
    xml = xml + '</stringRestriction>\n'
    xml = xml + '<data>\n'
    xml = xml + '<key>extradata</key>\n'
    xml = xml + '<value>{"name": "Mail Subject", "type": "string"}</value>\n'
    xml = xml + '</data>\n'
    xml = xml + '</field>\n'

    xml = xml + '<field>\n'
    xml = xml + '<name>ms_mail_message</name>\n'
    xml = xml + '<type>string</type>\n'
    xml = xml + '<stringRestriction>\n'
    xml = xml + '<maxLength>5000</maxLength>\n'
    xml = xml + '</stringRestriction>\n'
    xml = xml + '<data>\n'
    xml = xml + '<key>extradata</key>\n'
    xml = xml + '<value>{"name": "Mail message", "type": "textarea"}</value>\n'
    xml = xml + '</data>\n'
    xml = xml + '</field>\n'

    xml = xml + '<field>\n'
    xml = xml + '<name>ms_sharing_status</name>\n'
    xml = xml + '<type>string-exact</type>\n'
    xml = xml + '<data>\n'
    xml = xml + '<key>extradata</key>\n'
    xml = xml + '<value>{"name": "Sharing Status", "default": "None", "values": [ {"value": "None", "key": "None"}, {"value": "QuickLink Active", "key": "QuickLink Active"}, {"value": "File Too Big", "key": "File Too Big"}, {"value": "QuickLink Expired", "key": "QuickLink Expired"}, {"value": "File Uploaded", "key": "File Uploaded"}, {"value": "Uploading", "key": "Uploading"}, {"value": "Transcoding", "key": "Transcoding"}, {"value": "Published", "key": "Published"}, {"value": "Started Sharing Process", "key": "Started Sharing Process"} ], "type": "dropdown" }</value>\n'
    xml = xml + '</data>\n'
    xml = xml + '</field>\n'

    xml = xml + '<group>\n'
    xml = xml + '<name>Comment</name>\n'
    xml = xml + '<data>\n'
    xml = xml + '<key>extradata</key>\n'
    xml = xml + '<value>{"field_order": [ "ms_comment_date", "ms_comment_mail", "ms_comment", "ms_comment_id" ] }</value>\n'
    xml = xml + '</data>\n'

    xml = xml + '<field>\n'
    xml = xml + '<name>ms_comment_date</name>\n'
    xml = xml + '<type>string</type>\n'
    xml = xml + '<data>\n'
    xml = xml + '<key>extradata</key>\n'
    xml = xml + '<value>{"name": "Date of Comment", "type": "string" }</value>\n'
    xml = xml + '</data>\n'
    xml = xml + '</field>\n'

    xml = xml + '<field>\n'
    xml = xml + '<name>ms_comment_mail</name>\n'
    xml = xml + '<type>string</type>\n'
    xml = xml + '<data>\n'
    xml = xml + '<key>extradata</key>\n'
    xml = xml + '<value>{"name": "Mail Address", "type": "string" }</value>\n'
    xml = xml + '</data>\n'
    xml = xml + '</field>\n'

    xml = xml + '<field>\n'
    xml = xml + '<name>ms_comment</name>\n'
    xml = xml + '<type>string</type>\n'
    xml = xml + '<data>\n'
    xml = xml + '<key>extradata</key>\n'
    xml = xml + '<value>{"name": "Comment", "type": "textarea" }</value>\n'
    xml = xml + '</data>\n'
    xml = xml + '</field>\n'

    xml = xml + '<field>\n'
    xml = xml + '<name>ms_comment_id</name>\n'
    xml = xml + '<type>string</type>\n'
    xml = xml + '<data>\n'
    xml = xml + '<key>extradata</key>\n'
    xml = xml + '<value>{"name": "Comment ID", "type": "string" }</value>\n'
    xml = xml + '</data>\n'
    xml = xml + '</field>\n'

    xml = xml + '</group>\n'
    xml = xml + '</group>\n'

    xml = xml + "</MetadataFieldGroupDocument>"

    # print xml

    log.debug("We send the following XML file to Portal to create our md fields: %s." % xml)

    # Now that we generated our xml file, we send it to Portal.
    headers = {'Content-Type': 'application/xml'}
    r = requests.put("http://localhost:8080/API/metadata-field/field-group/MediaSilo/",
                     data=xml, auth=(conf.portal_user, conf.portal_pass), headers=headers)
    if r.status_code in [200, 204]:
        log.info("Seems like we successfully created necessary MediaSilo metadata fields in Portal.")
    else:
        log.info("Something went wrong during MediaSilo metadata field creation in Portal.")
        log.info(r.status_code)
        # log.debug(r.raise_for_status())
        sys.exit(1)
