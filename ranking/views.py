from ranking.models import SingleMatch, Result, Ranking, calculate_ranking
from ranking.forms import EnterSingleMatchResultForm
from comments.forms import CommentForm
from accounts.models import PlayerProfile
from user_messages.views import compose

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.template.context import RequestContext
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, get_object_or_404

from datetime import datetime



@login_required
def challenge_result (request, plr_id, mat_id):
    """
    Sends a message to player with profile 'plr_id' about
    challenging the result of match 'mat_id'.-
    """
    p = get_object_or_404 (PlayerProfile, pk=plr_id)
    m = get_object_or_404 (SingleMatch, pk=mat_id)
    # 
    # mark this match as being challenged
    #
    m.is_challenged = True
    m.save ( )
    #
    # and recalculate the players' ranking
    # through the callback function for new matches
    #
    calculate_ranking (sender=SingleMatch,
                       instance=m,
                       created=True)
    subject = '[%s] %s %s %s %s' % (_('Challenge'),
                                    _('About'),
                                    m.result,
                                    _('played on'),
                                    m.date)
    return compose (request,
                    recipient=p.user_profile.user.username,
                    subject=subject)
   
    
def comment_match (request, id):
    """
    Displays all comments of the match with 'id'. 
    If a user is logged-in, it also displays the form to enter
    a new comment about the match.-
    """
    match = get_object_or_404 (SingleMatch, pk=id)
    if (request.method == 'POST'):
        form = CommentForm (match, 
                            request.POST, 
                            request.FILES)
        if (form.is_valid ( )):
            form.instance.save ( )
    else:
        form = CommentForm (match)
        
    return render_to_response ('ranking/comment_match.html',
                               {'match': match,
                                'form': form,
                                'next': reverse('ranking.views.comment_match', args=[id])},
                               context_instance=RequestContext(request))
    
    
def display_ranking (request):
    """
    Displays the players' ranking.-
    """
    ranking = Ranking.objects.all ( ).order_by ('-points')
    return render_to_response ('ranking/ranking.html',
                               {'rank_list': ranking},
                               context_instance=RequestContext(request))
    
    
def display_matches (request, id):
    """
    Display the matches played by user with 'id'.-
    """
    other_user = get_object_or_404 (User, pk=id)
    return render_to_response ('ranking/display_matches.html',
                               {'other_user': other_user,
                                'form': None},
                               context_instance=RequestContext(request))
    
    
@login_required
def enter_result (request):
    """
    Adds the result of a singles match between two players.-
    """
    match_list = SingleMatch.objects.get_results (request.user.id)
    form = EnterSingleMatchResultForm (request.POST or None,
                                       usr=request.user) 
    if form.is_valid ( ):
        sm = SingleMatch ( )
        sm.date = datetime.today ( )
        
        usr = request.user.get_profile ( ).player_profile
        opp = PlayerProfile.objects.get (pk=form.cleaned_data['opponent'].pk)
        
        if (form.cleaned_data['user_won'] == 'Y'):
            sm.winner = usr
            sm.loser = opp
        else:
            sm.winner = opp
            sm.loser = usr
        #
        # save the score info
        #
        r = Result ( )
        r.type = form.cleaned_data['type']
        r.score = form.cleaned_data['score']
        r.save (force_insert=True)
        #
        # save into the DB
        #
        sm.result = r
        sm.save (force_insert=True)
        
    return render_to_response ('ranking/display_matches.html',
                               {'match_list': match_list.iterator,
                                'form': form},
                               context_instance=RequestContext(request))
    
