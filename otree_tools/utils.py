from otree.models_concrete import PageCompletion
from otree_tools.models import Enter, Exit, FocusEvent, focus_enter_codes, focus_exit_codes
from datetime import timedelta
import logging
from django.db.models import F, ExpressionWrapper, DurationField, Sum, IntegerField, Value
from otree_tools import cp
from django.db.models.functions import Cast

logger = logging.getLogger('otree_tools.time.utils')


def get_seconds_per_page(player, page_name, ):
    participant = player.participant
    subsession_pk = player.subsession.pk
    try:
        page_info = PageCompletion.objects.get(participant=participant, subsession_pk=subsession_pk,
                                               page_name=page_name)
    except PageCompletion.DoesNotExist:
        raise ValueError('Cannot find info about this page')
    return page_info.seconds_on_page


def get_time_per_page(player, page_name):
    """Returns time per page as measured by tracking_time tag on a corresponding page."""

    q = Exit.objects. \
        filter(player_id=player.pk,
               participant=player.participant,
               page_name=page_name,
               enter__isnull=False,
               )

    tot_exits = q.aggregate(diff=Sum(ExpressionWrapper(F('timestamp') - F('enter__timestamp'),
                                                       output_field=DurationField())))['diff']

    if tot_exits:
        return tot_exits.total_seconds()
    else:

        diffs = [i.timestamp-i.enter.timestamp for i in q]
        sum_dif = sum(diffs, timedelta())
        return sum_dif.total_seconds()



def get_focused_time(player, page_name):
    return FocusEvent.objects.get_focused_time_per_page(player.id, player.participant.id, page_name)


def get_unfocused_time(player, page_name):
    return FocusEvent.objects.get_unfocused_time_per_page(player.id, player.participant.id, page_name)


def num_focusoff_events(player, page_name):
    return FocusEvent.objects.num_focusoff_events(player.id, player.participant.id, page_name)
