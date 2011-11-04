from django.db import models



class City (models.Model):
    """
    A simple container for the cities of the country.-
    """
    name = models.CharField (max_length=100,
                             null=False,
                             blank=False)
    
    def __unicode__ (self):
        return self.name
    
