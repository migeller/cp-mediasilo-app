from django.db import models
from django.utils.translation import ugettext as _

'''
CP MediaSilo App plugin model.
More info: https://docs.djangoproject.com/en/dev/topics/db/models/
'''


class CPMSAConfigModel(models.Model):

    """ Definition of a plugin model.
    """

    class Meta:
        verbose_name = _("CP MediaSilo App Model")
        verbose_name_plural = _("CP MediaSilo App Model")

    def __unicode__(self):
        _name = " (" + self.external_id + ")"
        return _name
