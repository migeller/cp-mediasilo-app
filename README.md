# cp-mediasilo-app
connects Cantemo Portal to MediaSilo for review and approval workflows


# Introduction
This paper describes the installation, configuration and usage of moosystems’ CP MediaSilo App, which allows sharing files from within Cantemo Portal via MediaSilo’s cloud-based QuickLinks.
Using this app Portal transcodes web-optimized versions of your selected files, uploads them to MediaSilo’s cloud storage and sends emails to let people access password-protected web pages, on which they can view and annotate your media.
You get informed via email each time someone watches your media, and annotations get synced back to your item’s metadata in Portal, so your Portal users never need to leave their Portal environment to share media with customers and external coworkers.
In addition, Portal will track which items are currently being shared with who and will preserve all comments made on your items. This way you will always know exactly when an item has been shared with who. Sharing history will be tracked at a central point, now.
One of the reasons why this app was written is that before version 2.0 Portal had no sharing function at all. The CP MediaSilo App works with Portal 1.6.5 or later, which means you can easily extend your existing Portal environment without the need to update Portal itself.
Portal 2.0 introduces sharing functionality on its own. While this is a great feature, it means you need to either put Portal into the cloud or –if you use it on-premise like most people do– you need to open your firewall to let external partners access your Portal system.
If you are a big company, your firewall administrators might not want to open the ports needed due to security policies. If you are a small company, your upload bandwidth might be too slow to deliver previews to external partners.
No matter if you are big or small, making your whole Portal system accessible from the Internet might not provide the security you are looking for.
Using the CP MediaSilo App to share media with external partners means that you only upload media to the cloud which you really need to share. In a resolution and quality which is great for review &  approval workflows, but you never share the original files across the Internet.
We think that using a hybrid solution made of on-premise and cloud-based tools combines the best of both worlds.
Another great feature of the CP MediaSilo App is that other than Portal 2.0’s internal sharing feature it can not only share single files but anything from a single file to your whole Portal library.

# Changelog
version 1.0.4
release date: 24.08.2015
Supports non-ASCII characters in mail subject and mail message.

version 1.0.3
release date: 16.06.2015
Doesn’t matter anymore which network interface uses the licensed MAC address.

version 1.0.2
release date: 11.02.2015
Supports Vidispine 4.2.4 and Portal 2.0.1
fixes a bug where multiple mail recipients received separate QuickLinks

version 1.0.1
release date: 09.02.2015
Using the new MediaSilo upload module to improve security and stability.
supports uploading files up to 5GB in size
supports uploading files with non-ascii UTF-8 characters in filename

version 1.0
release date: 27.11.2014
Initial version.

# Requirements
Before you can use the CP MediaSilo App, you need to make sure that Cantemo Portal is already up and running, and you need a MediaSilo account.
The CP MediaSilo App runs on CentOS 6.x and support Cantemo Portal 1.6.x and 2.x.

# CP MediaSilo App Installation
# Preparation
Clone this repository onto your Portal machine and cd into the installer directory. Type `install.py` and the installer will tell you how to proceed.

# Configure the CP MediaSilo App
Please open your Portal metadata section at http://PORTAL_IP_ADDRESS/vs/metadatamanagement/ and select your top-level metadata group. For example, when you migrated a Final Cut Server system to Portal (which can easily be done using moosystems’ CP Migration Tool), your top-level metadata group is called “Final Cut Server”:

Choose “Groups” from the left-hand side and move the “MediaSilo” group into your metadata group.
Your main metadata group will now contain all metadata fields needed to store MediaSilo relevant metadata:

When you select the MediaSilo group like displayed in the screenshot above, make sure to set “Occurrence Minimum” to 0 and “Occurrence Maximum” to 1.
Do the same thing for any top-level metadata groups you are using.
Now make sure that all users, who are allowed to share media via MediaSilo are in the CPMediaSiloApp group and use a main metadata group as default which has MediaSilo metadata set up like above:

Portal only displays “Send QuickLink” options to users who are members of the CPMediaSiloApp group.
In addition make sure that the default metadata group of your users is a metadata group which contains MediaSilo metadata fields.
Now open the CP MediaSilo App settings in Portal’s admin section:

Please enter your MediaSilo credentials, which come with your MediaSilo account. If e.g. you access your MediaSilo site via https://moosystems.mediasilo.com, your mediaSilo hostname is moosystems.
Save your settings.
Then go back to your Terminal and start the CP MediaSilo App daemon:
service cpmsa start
If you click on “Logs” in your CP MediaSilo App settings, you can see that your daemon is working in the background:

Now click on “CP MediaSilo App” again and select your default MediaSilo project. All items you are going to share later on will be uploaded into that project. Save your settings.
In case you start with a brand-new MediaSilo account, you need to create your first project beforehand in MediaSilo:

Now switch to the “Transcode Profiles” section in the Portal admin panel and make sure that our installer created a “MediaSilo” transcode setting:

Every time we upload a file to MediaSilo, Portal uses this profile to create a 3Mb mp4 file in 720p resolution.
Where Can I Share What?
Each item and collection as well as all action gears allow you to archive and restore assets.
You can select single items or multiple items in the search results list or in the bin, as well as entire collections, even multiple collections at the same time:


# The Sharing Process
Let’s look at how you share media via MediaSilo, now.
Select one or more items in your search results and open the action gear menu in the upper right corner of the Portal interface. You can also select an item’s action gear menu or the bin’s action gear menu.
Choose “Send QuickLink” (see screenshot above). This opens our “Send QuickLink” dialog:

Please enter one or more recipient email addresses. If you enter more than one address, separate them using commas.
You can optionally enter a mail subject and message.
Please add an expiry date. After that date the QuickLink will expire and users can not view and annotate the items related to that QuickLink anymore.
The items will reside on MediaSilo after a QuickLink has expired, as you might want to share an item in additional QuickLinks without the need to upload files multiple times.
When you click “Send”, Portal will confirm that the Sharing Process has started. If now you look at the item’s metadata, you will find sharing related metadata:

Reload the page to see the current sharing status. Now the CP MediaSilo App checks if the item has already been uploaded to MediaSilo. If yes, it will only create a new QuickLink pointing to the new item.
If the item has not been shared, yet, Portal creates a web-optimized version of your item and sets the sharing status to “Transcoding”. You can monitor the transcoding status in the Portal jobs section:

When the transcoding has finished, the item will be uploaded to MediaSilo and its sharing status will be set to “Uploading”. In the items “Formats” section you will now find a new MediaSilo format:

After that the QuickLink will be created, and the sharing status will be set to “QuickLink Active.”
MediaSilo will send invitation mails to the recipients you selected, which will include a thumbnail, your message, the url to the QuickLink as well as a random password generated by the CP MediaSilo App:

If a user clicks on the QuickLink, he will need to provide the password included in the email:

Now the user can view the item. To add annotations, the user can log in to MediaSilo using a MediaSilo account, via Google+ or Facebook, or simply by providing Name and email details.
Now the user can add comments:

which will automatically be synced back to your item’s Portal metadata:

In addition, MediaSilo sends you emails whenever someone views or annotates one of your shared items:

Once a QuickLink expires, the CP MediaSilo App sets the sharing status to “QuickLink Expired”.
You can search for sharing status values and e.g. list all items which are currently being shared via MediaSilo:

# Technical Details And Logging
The main work is being done by the CP MediaSilo App daemon, which resides at /usr/local/cpmsa/main.py
You can start and stop it on the command-line by invoking one of these commands:
service cpaa start
service cpaa stop
To see what the app is doing, you can read its logs on the Portal server:
tail -f /usr/local/cpmsa/daemon.log
This will give you quite verbose information about what’s going on.
The same log will be displayed in the CP MediaSilo App log section of the Portal admin UI, now (see above).

# API
If you want to trigger sharing of items using your own tools, there’s an API available, which can be accessed from tools running on the Portal server. Please read the source code to understand the API.

# Uninstall CP MediaSilo App
To uninstall the CP MediaSilo App, open the installer folder you extracted in the beginning of this paper and run the uninstaller in the command-line. Before you do this, stop the CP MediaSilo App daemon:
service cpmsa stop
uninstall.py —portal_user=admin —portal_pass=admin
