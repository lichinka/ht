from django.db import models
from django.contrib.auth.models import User


class Article (models.Model):
    """
    Represents an article in the Wiki area of the site.-
    """
    title = models.CharField (max_length=255,
                              unique=True)
    text = models.TextField ( )
    
    def __unicode__ (self):
        return self.title


class ChangeLog (models.Model):
    """
    Saves the change history of a wiki article.-
    """
    user = models.ForeignKey (User)
    article = models.ForeignKey (Article)
    when = models.DateTimeField (null=False,
                                 blank=False)
    diff = models.TextField ( )

    def __unicode__ (self):
        return "%s - %s: %s" % (self.user.username,
                                self.article,
                                self.when)
        