from django.db import models
from django.utils.translation import ugettext_lazy as _


class City (models.Model):
    """
    A simple container for the cities of the country.-
    """
    name = models.CharField (max_length=100,
                             null=False,
                             blank=False)
    class Meta:
        ordering = ['name']
        verbose_name = _('City')
        verbose_name_plural = _('Cities')
         
    def __unicode__ (self):
        return self.name
    
