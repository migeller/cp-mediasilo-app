from django import forms
from models import CPMSAConfigModel
from os import getcwd
from os import path
import json
import logging
import codecs
import requests
log = logging.getLogger(__name__)

'''
Here we define the forms used by the CP MediaSilo App
'''


class CPMSAConfigForm(forms.ModelForm):

    """ Main form for adding and editing CPMediaSiloAppModel"""
    required_css_class = 'required'

    class Meta(object):
        model = CPMSAConfigModel
        # exclude = ('external_id')

    def __init__(self, *args, **kwargs):
        forms.ModelForm.__init__(self, *args, **kwargs)

        # read the config file if it already exists
        configfile = getcwd() + '/plugins/CPMediaSiloApp/config.json'

        if path.isfile(configfile):

            with open(configfile, "r") as config_file:

                try:
                    config = json.loads(config_file.read())
                except:
                    log.info("Can't read the config file at %s." % configfile)
                    return

                # get the MediaSilo hostname, e.g. "moosystems"
                self.ms_hostname = config["ms_hostname"]

                # get the MediaSilo username, e.g. "aaulich"
                self.ms_username = config["ms_username"]

                # get the MediaSilo user password.
                self.ms_password = config["ms_password"]

                # check if all media shall be synced to MediaSilo
                # self.sync_all = config["sync_all"]

                # check which MediaSilo project shall be used
                # as default upload location
                self.default_project = config["default_project"]

        else:

            with open(configfile, "w") as config_file:

                # set the MediaSilo hostname.
                self.ms_hostname = ""

                # set the MediaSilo username.
                self.ms_username = ""

                # set the MediaSilo password.
                self.ms_password = ""

                # set sync all to MediaSilo to no.
                # self.sync_all = False

                # set MediaSilo default project to none
                self.default_project = "none"

                # create a dictionary which we can convert to json and write to
                # our config file
                my_config = {}
                my_config["ms_hostname"] = self.ms_hostname
                my_config["ms_username"] = self.ms_username
                my_config["ms_password"] = self.ms_password
                my_config["default_project"] = self.default_project

                # Now convert our config to json and write it to file
                json.dump(my_config, config_file)

        self.fields["ms_hostname"] = forms.CharField(
            required=True, widget=forms.widgets.TextInput())
        self.fields["ms_hostname"].label = "MediaSilo Hostname"
        self.fields["ms_hostname"].initial = self.ms_hostname

        self.fields["ms_username"] = forms.CharField(
            required=True, widget=forms.widgets.TextInput())
        self.fields["ms_username"].label = "MediaSilo Username"
        self.fields["ms_username"].initial = self.ms_username

        self.fields["ms_password"] = forms.CharField(
            required=True, widget=forms.PasswordInput(render_value=True))
        self.fields["ms_password"].label = "MediaSilo Password"
        self.fields["ms_password"].initial = self.ms_password

        # here we fetch all projects available on our MediaSilo page:
        # Most of the following variables are derived from the variables above
        self.ms_url = "https://api.mediasilo.com/v3"
        self.ms_credentials = codecs.encode(
            "%s:%s" % (self.ms_username, self.ms_password),
            "base64").rstrip()
        headers = {"MediaSiloHostContext": self.ms_hostname,
                   "Authorization": "Basic %s" % self.ms_credentials,
                   'Content-Type': 'application/json',
                   'Accept': 'application/json'}

        url = "%s/projects" % self.ms_url
        reply = requests.get(url, headers=headers)
        try:
            content_of_reply = json.loads(reply.content)
        except:
            pass
        projects = (("none", "none"),)
        try:
            for i in content_of_reply:
                projects += ((i["name"], i["name"]),)
        except:
            pass


        self.fields["default_project"] = forms.ChoiceField(required=False,
                                                           choices=projects)
        self.fields["default_project"].label = "Default MediaSilo project"
        self.fields["default_project"].initial = self.default_project
