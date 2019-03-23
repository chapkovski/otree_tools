from otree.models_concrete import PageCompletion
from otree_tools.models import Enter, Exit, FocusEvent, focus_enter_codes, focus_exit_codes
from datetime import timedelta
import logging
from django.db.models import F, ExpressionWrapper, DurationField, Sum
from otree_tools import cp

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

    tot_exits = Exit.objects.filter(player_id=player.pk,
                                    participant=player.participant,
                                    page_name=page_name,
                                    enter__isnull=False,
                                    ).aggregate(diff=Sum(ExpressionWrapper(F('timestamp') - F('enter__timestamp'),
                                                                           output_field=DurationField())))['diff']
    if tot_exits:
        return tot_exits
    else:
        return timedelta()


def get_focus_tracker_data(player, page_name, focus_type):
    tot_exits = FocusEvent.objects.filter(player_id=player.pk,
                                          participant=player.participant,
                                          page_name=page_name,
                                          entry__isnull=False,
                                          event_num_type__in=focus_type,
                                          ).aggregate(diff=Sum(ExpressionWrapper(F('timestamp') - F('entry__timestamp'),
                                                                                 output_field=DurationField())))['diff']
    if tot_exits:
        return tot_exits
    else:
        return timedelta()


def get_focused_time(player, page_name):
    return get_focus_tracker_data(player, page_name, focus_exit_codes)


def get_unfocused_time(player, page_name):
    return get_focus_tracker_data(player, page_name, focus_enter_codes)
