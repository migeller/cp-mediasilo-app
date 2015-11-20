"""
URLS for the CP MediaSilo App plugin
"""

from django.conf.urls.defaults import *

urlpatterns = patterns('portal.plugins.CPMediaSiloApp',
                       url(r'^publish/$', 'cpmediasiloapp.Publish',
                           name='publish',
                           kwargs={'template': 'response.html'}),
                       url(r'^$',
                           'cpmediasiloapp.CPMediaSiloAppConfigurationView',
                           name='cp_mediasilo_app_config',
                           kwargs={'template': 'cp_mediasilo_app_model_view.html'}),
                       url(r'^DisplayMenuEntry/$',
                           'cpmediasiloapp.DisplayMenuEntry',
                           name='DisplayMenuEntry',
                           kwargs={'template': 'publish_view.html'}),
                       url(r'^cpmsa_logs/$',
                           'cpmediasiloapp.CPMSALogs',
                           name='cpmsa_logs',
                           kwargs={'template': 'cpmsa_logs.html'}),
                       url(r'^read_cpmsa_logs/$',
                           'cpmediasiloapp.ReadCPMSALogs',
                           name='read_cpmsa_logs',
                           kwargs={'template': 'read_cpmsa_logs.html'}),
                       url(r'^show_plugin/$', 'cpmediasiloapp.ShowPlugin',
                           name='show_plugin',
                           kwargs={'template': 'show_plugin_view.html'})
                       )
