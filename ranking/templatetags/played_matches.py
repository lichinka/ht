from ranking.models import SingleMatch

from django import template

register = template.Library ( )


@register.inclusion_tag('ranking/played_matches.html')
def played_matches (user):
    """
    Renders a list of matches played by the received player 'user'.-
    """
    match_qset = SingleMatch.objects.get_results (user)
    return {'match_qset': match_qset}
