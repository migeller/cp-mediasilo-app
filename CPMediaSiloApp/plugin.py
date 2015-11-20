from portal.pluginbase.core import *
from portal.generic.plugin_interfaces import IPluginURL,\
    IPluginBlock, IContextProcessor, IAppRegister

import logging
log = logging.getLogger(__name__)


"""
register the CP MediaSilo App in the Portal Admin panel
"""


class CPMediaSiloAppRegister(Plugin):

    implements(IAppRegister)

    def __init__(self):
        self.name = "CP MediaSilo App"
        self.plugin_guid = "900EF5FC-A112-403B-A6C2-4B7810B3A943"
        log.debug("Registered CP MediaSilo App.")

    def __call__(self):
        _app_dict = {
            "name": self.name,
            "version": "1.0.4",
            "author": "Andre Aulich moosystems",
            "author_url": "moosystems.com",
            "notes": "Copyright 2015. All Rights Reserved."}
        return _app_dict

cpmediasiloappplugin = CPMediaSiloAppRegister()


'''
URL Plugin that defines new URLs in the system
'''


class CPMediaSiloAppURL(Plugin):

    """ Loads the Admin rules URLs
    """
    implements(IPluginURL)

    def __init__(self):
        self.name = "CPMediaSiloAppURL"
        # Should point to the urls.py
        self.urls = 'portal.plugins.CPMediaSiloApp.urls'
        # Defines the URL pattern prefix
        self.urlpattern = r'^cpmediasiloapp/'
        # Defines the plugin namespace
        self.namespace = 'cpmediasiloapp'
        # Define a GUID for each plugin.
        # Use e.g. http://www.guidgenerator.com/
        self.plugin_guid = "6F228692-D60C-4A98-B541-D01DE79B4D19"
        log.debug("Initiated CPMediaSiloAppURL.")

# Load the URL plugin
pluginurls = CPMediaSiloAppURL()


'''
Block plugin which defines new functionalities and workflows in the system
'''


class CPMediaSiloAppBlock(Plugin):

    implements(IPluginBlock)

    def __init__(self):

        self.name = "AdminLeftPanelBottomPanePlugin"
        # Define a GUID for each plugin.
        # Use e.g. http://www.guidgenerator.com/
        self.plugin_guid = "BE524FF4-4E20-412A-8976-6FBDEC544058"
        log.debug("Initiated CPMediaSiloAppBlock.")

    def return_string(self, tagname, *args):
        return {'guid': self.plugin_guid,
                'template': 'admin_leftpanel_entry.html'}

pluginblock = CPMediaSiloAppBlock()


class CPMediaSiloAppNavBarPlugin(Plugin):

    implements(IPluginBlock)

    def __init__(self):
        """The name of the plugin which should match the pluginblock tag
        in the Portal template. For instance as defined in navigation.html:
        {% pluginblock "NavigationAdminPlugin" sand %}
        This plugin is placed in the admin navigation bar."""
        self.name = "NavigationAdminPlugin"
        # Define a GUID for each plugin.
        # Use e.g. http://www.guidgenerator.com/
        self.plugin_guid = "0A0AD5D5-4CA0-427E-ACB5-74E56254B2FD"
        log.debug("Initiated CPMediaSiloAppNavBarPlugin.")

    def return_string(self, tagname, *args):
        return {'guid': self.plugin_guid, 'template': 'navigation_admin.html'}

pluginblock = CPMediaSiloAppNavBarPlugin()


class CPMediaSiloAppGearboxMenuPlugin(Plugin):
    implements(IPluginBlock)

    def __init__(self):
        """The name of the plugin which should match the pluginblock tag
        in the Portal template. For instance as defined in media_view.html:
        {% pluginblock "MediaViewDropdown" %}
        This plugin is placed in the gearbox menu for the item."""
        self.name = "MediaViewDropdown"
        # Define a GUID for each plugin.
        # Use e.g. http://www.guidgenerator.com/
        self.plugin_guid = "1CCC5696-F5AA-44E2-B6CA-D68B0E5D2931"
        log.debug("Initiated CPMediaSiloAppGearboxMenuPlugin.")

    def return_string(self, tagname, *args):
        return {'guid': self.plugin_guid, 'template': 'gearbox_menu.html'}

pluginblock = CPMediaSiloAppGearboxMenuPlugin()


class ItemContextPlugin(Plugin):
    implements(IContextProcessor)

    def __init__(self):
        self.name = "ItemContextPlugin"
        # Define a GUID for each plugin.
        # Use e.g. http://www.guidgenerator.com/
        self.plugin_guid = "1042462E-A8A9-4004-9732-C1F141B7A16C"
        log.debug("Initiated ItemContextPlugin.")

    def __call__(self, context, class_object):
        from portal.vidispine.vitem import ItemView
        if isinstance(class_object, ItemView) is False:
            return context

        self.context = context
        self.class_object = class_object
        #self.username = "test"
        return self.process_context()

    def process_context(self):
        return self.context

contextplugin = ItemContextPlugin()


class CPMediaSiloAppGearboxCollectionMenuPlugin(Plugin):
    implements(IPluginBlock)

    def __init__(self):
        """The name of the plugin which should match the pluginblock tag
        in the Portal template. For instance as defined in media_view.html:
        {% pluginblock "MediaViewDropdown" %}
        This plugin is placed in the gearbox menu for the item."""
        self.name = "CollectionViewDropdown"
        # Define a GUID for each plugin.
        # Use e.g. http://www.guidgenerator.com/
        self.plugin_guid = "9C7AF4B1-895A-4065-986D-6518A949FAB"
        log.debug("Initiated Collection Menu Gear Box.")

    def return_string(self, tagname, *args):
        return {'guid': self.plugin_guid, 'template': 'gearbox_menu_big.html'}

pluginblock = CPMediaSiloAppGearboxCollectionMenuPlugin()


class CPMediaSiloAppGearboxBinMenuPlugin(Plugin):
    implements(IPluginBlock)

    def __init__(self):
        """The name of the plugin which should match the pluginblock tag
        in the Portal template. For instance as defined in media_view.html:
        {% pluginblock "MediaViewDropdown" %}
        This plugin is placed in the gearbox menu of the bin."""
        self.name = "MediaBinDropdown"
        # Define a GUID for each plugin.
        # Use e.g. http://www.guidgenerator.com/
        self.plugin_guid = "4EEB8178-E02E-4CD8-A8F9-CDAB1031EEC0"
        log.debug("Initiated MediaBinDropdown.")

    def return_string(self, tagname, *args):
        return {'guid': self.plugin_guid, 'template': 'gearbox_menu_bin.html'}

pluginblock = CPMediaSiloAppGearboxBinMenuPlugin()


class CPMediaSiloAppGearboxCollectionSearchMenuPlugin(Plugin):
    implements(IPluginBlock)

    def __init__(self):
        """The name of the plugin which should match the pluginblock tag
        in the Portal template. For instance as defined in media_view.html:
        {% pluginblock "MediaViewDropdown" %}
        This plugin is placed in the gearbox menu for the item."""
        self.name = "CollectionSearchViewDropdown"
        # Define a GUID for each plugin.
        # Use e.g. http://www.guidgenerator.com/
        self.plugin_guid = "7A4A3912-604E-455A-9E17-F34CADA0BC32"
        log.debug("Initiated Collection Search View DropDown.")

    def return_string(self, tagname, *args):
        return {'guid': self.plugin_guid, 'template': 'gearbox_menu_big.html'}

pluginblock = CPMediaSiloAppGearboxCollectionSearchMenuPlugin()


class CPMediaSiloAppGearboxSearchViewMenuPlugin(Plugin):
    implements(IPluginBlock)

    def __init__(self):
        self.name = "SearchViewDropdown"
        self.plugin_guid = "3CDDEED9-73E3-45AC-9835-C6A5480B3BA2"
        log.debug("Initiated SearchViewDropdown.")

    def return_string(self, tagname, *args):
        return {'guid': self.plugin_guid, 'template': 'gearbox_menu_big.html'}

pluginblock = CPMediaSiloAppGearboxSearchViewMenuPlugin()
