# -*- coding: utf-8 -*-

from portal.generic.baseviews import ClassView

import logging
import os
import urllib2
import base64
import json
import socket

log = logging.getLogger(__name__)


def check_membership(username):
    """This function checks if the current user is in the group CPMediaSiloApp.
    Only members of this group can publish media items to MediaSilo."""
    # log.info("2.")
    # get the Vidispine user name.
    with open("/etc/cantemo/portal/portal.conf", "r") as portal_cfg_file:
        # print portal_cfg_file.readlines()
        for line in portal_cfg_file.readlines():
            if "VIDISPINE_USERNAME" in line:
                portal_user = line.split(" ")[2].rstrip()
            if "VIDISPINE_PASSWORD" in line:
                portal_pwd = line.split(" ")[2].rstrip()
    url = 'http://localhost:8080/API/user/' + str(username) + '/groups'
    request = urllib2.Request(url)
    base64string = base64.encodestring(
        '%s:%s' % (portal_user, portal_pwd)).replace('\n', '')
    request.add_header("Authorization", "Basic %s" % base64string)
    request.add_header("Accept", "application/xml")
    result = urllib2.urlopen(request)
    response = result.read()

    if not "CPMediaSiloApp" in response:
        return False
    else:
        return True


class DisplayMenuEntry(ClassView):

    """Only display entry "Publish on MediaSilo" in action menu of an item
    if group membership is correct."""

    def __call__(self):
        self.template = os.getcwd() + \
            '/plugins/CPMediaSiloApp/templates/publish_view.html'
        # log.info(self.request.user)
        if check_membership(self.request.user) is True:
            log.info("User %s is in CPMediaSiloApp group." % self.request.user)
            return self.main(self.request, self.template, {"member": "True"})
        else:
            log.info("User %s is not in CPMediaSiloApp group." %
                     self.request.user)
            return self.main(self.request, self.template, {"member": "False"})


class Publish(ClassView):

    """"When a user hits 'Publish on MediaSilo' in the Portal UI,
    this triggers the publishing process."""

    def __call__(self):
        # Read some data from our config file.
        with open("/etc/cantemo/portal/portal.conf", "r") as portal_cfg_file:
        # print portal_cfg_file.readlines()
            for line in portal_cfg_file.readlines():
                if "VIDISPINE_USERNAME" in line:
                    portal_user = line.split(" ")[2].rstrip()
                if "VIDISPINE_PASSWORD" in line:
                    portal_pwd = line.split(" ")[2].rstrip()

        # set the port for our daemon.
        daemon_port = 56912


        # figure out if we deal with collections or items and get their ids
        if "type" in self.request.GET:
            type = self.request.GET["type"]
        else:
            if "type" in self.request.POST:
                type = self.request.POST["type"]
            else:
                type = "items"

        try:
            recipient_mail = self.request.POST['recipient_mail']
        except:
            recipient_mail = ""

        try:
            mail_subject = self.request.POST['mail_subject']
        except:
            mail_subject = ""

        try:
            mail_message = self.request.POST['mail_message']
        except:
            mail_message = ""

        try:
            expiry_date = self.request.POST['expiry_date']
        except:
            expiry_date = ""


        # here we deal with collections
        if type == "collections":
            collection_list = self.request.POST.getlist('item_id[]')
            itemid = collection_list
            log.info("Looking at collection(s) '%s'." % itemid)

        else:
            # here we deal with items
            if 'binmenu' in self.request.POST:

                url = 'http://127.0.0.1:80/API/v1/mediabin?limit=0'

                request = urllib2.Request(url)
                base64string = base64.encodestring(
                    '%s:%s' % (portal_user, portal_pwd)).replace('\n', '')
                request.add_header("Authorization", "Basic %s" % base64string)
                request.add_header("Accept", "application/json")
                result = urllib2.urlopen(request)

                response = result.read()

                decoded = json.loads(response)

                itemid = []
                for item in decoded["objects"]:
                    # log.info("item: '%s'" % item)
                    itemid.append(item["resource_id"])


            else:
                if 'item_id' in self.request.GET:
                    itemid = self.request.GET['item_id']
                else:
                    try:
                        itemid = self.request.POST['item_id']
                    except:
                        extra_context = {
                            'response': "You haven't selected any items."
                        }
                        # log.critical("self.request: %s" % self.request)
                        # log.critical("self.template: %s" % self.template)
                        # log.critical("extra content: %s" % extra_context)
                        return self.main(self.request, self.template, extra_context)
            log.info("itemid: '%s'" % itemid)

            if not isinstance(itemid, list) and "_" in itemid:
                itemid = itemid.split("_")
            elif not isinstance(itemid, list) and " " not in itemid:
                my_string = itemid
                itemid = list()
                itemid.append(my_string)
            log.info("itemid: '%s'" % itemid)

        # here we build the json document we send to our daemon
        if type == "items":
            message = {'items': itemid,
                       'recipient_mail': recipient_mail,
                       'mail_subject': mail_subject,
                       'mail_message': mail_message,
                       'expiry_date': expiry_date }

            # log.critical(message)
        else:
            message = {'collections': collection_list,
                       'recipient_mail': recipient_mail,
                       'mail_subject': mail_subject,
                       'mail_message': mail_message,
                       'expiry_date': expiry_date }

        message = json.dumps(message, ensure_ascii=True)
        log.info("message: %s" % message)

        # now we send the document to our daemon
        def client(ip, port, message):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((ip, daemon_port))
            try:
                sock.sendall(message)
                response = sock.recv(1024)
                return response
            finally:
                sock.close()

        response = client("localhost", daemon_port, message)
        log.info("The server responded %s." % response)

        extra_context = {
            'response': response
        }
        return self.main(self.request, self.template, extra_context)


class CPMediaSiloAppConfigurationView(ClassView):

    """ Here we write our CP MediaSilo App settings back to our config file
    """

    def __call__(self):
        refresh = ''
        from forms import CPMSAConfigForm
        import json
        import os
        if self.request.method == 'POST':
            _formconfig = CPMSAConfigForm(self.request.POST)

            if _formconfig.is_valid() is True:
                my_config = {}
                my_config["ms_hostname"] = _formconfig.cleaned_data[
                    "ms_hostname"]
                my_config["ms_username"] = _formconfig.cleaned_data[
                    "ms_username"]
                my_config["ms_password"] = _formconfig.cleaned_data[
                    "ms_password"]
                my_config["default_project"] = _formconfig.cleaned_data[
                    "default_project"]

                configfile = os.path.join(
                    os.getcwd(), 'plugins/CPMediaSiloApp/config.json')
                log.critical(configfile)
                log.critical(my_config)

                if os.path.isfile(configfile):
                    with open(configfile, "w") as config_file:
                        # convert our config to json and write it to file
                        json.dump(my_config, config_file)

                log.info("MediaSilo hostname: %s" % my_config["ms_hostname"])
                log.info("MediaSilo username: %s" % my_config["ms_username"])
                log.info("MediaSilo password: %s" % my_config["ms_password"])
                log.info("Default MediaSilo project: %s" %
                         my_config["default_project"])

            refresh = 'true'

        else:
            _formconfig = CPMSAConfigForm()

        ctx = {"form_config": _formconfig, "refresh": refresh}
        return self.main(self.request, self.template, ctx)


class CPMSALogs(ClassView):

    """Here we deal with the logs we need to display in the Portal UI"""

    def __call__(self):
        self.log_file = os.path.join("/", "usr",
                                     "local", "cpmsa", "daemon.log")
        self.log_content = os.popen("tail -1000 " + self.log_file).readlines()
        self.log_content.reverse()

        """ self.log_content = [ "Hello, here will be the log content.\
            Please update cpmediasiloapp.py class CPMSALogs to activate."]"""

        ctx = {"log_content": self.log_content}

        return self.main(self.request, self.template, ctx)


class ReadCPMSALogs(ClassView):

    """Here we deliver logs to the Log view in the Portal admin section. """

    def __call__(self):
        self.log_file = os.path.join("/", "usr",
                                     "local", "cpmsa", "daemon.log")
        self.log_content = os.popen("tail -1000 " + self.log_file).readlines()
        self.log_content.reverse()

        ctx = {"log_content": self.log_content}
        return self.main(self.request, self.template, ctx)


class ShowPlugin(ClassView):

    """tells if a user is member of the group CPMediaSiloApp"""

    def __call__(self):
        return self.main(self.request, self.template,
                         {"show_plugin": check_membership(self.request.user)})
