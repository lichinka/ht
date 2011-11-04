from django.forms import ModelForm
from wiki.models import Article

class EditArticleForm (ModelForm):
    """
    A form to edit the content of a wiki article.-
    """
    class Meta:
        model = Article