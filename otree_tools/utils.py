from otree.models_concrete import PageCompletion
from otree_tools.models import EnterEvent, FocusEvent, Marker
from django.db.models import Count, Min, Sum, Q, ExpressionWrapper, F, DurationField
from datetime import timedelta
import errno
import shutil
import logging
from django.utils import timezone


def copy(src, dest):
    try:
        shutil.copytree(src, dest)
        return True
    except OSError as e:
        # If the error was caused because the source wasn't a directory
        if e.errno == errno.ENOTDIR:
            shutil.copy(src, dest)
            return True
        else:
            logger = logging.getLogger('otree-tools')
            logger.error('Directory not copied. Error: {}'.format(e))
            return False


def get_seconds_per_page(player, page_name, ):
    participant = player.participant
    subsession_pk = player.subsession.pk
    try:
        page_info = PageCompletion.objects.get(participant=participant, subsession_pk=subsession_pk,
                                               page_name=page_name)
    except PageCompletion.DoesNotExist:
        raise ValueError('Cannot find info about this page')
    return page_info.seconds_on_page


def get_time_per_page(player, page_name, none_to_zero=False):
    tot_enter_events = EnterEvent.objects.filter(player_id=player.pk, participant=player.participant,
                                                 page_name=page_name
                                                 ).annotate(num_exits=Count('exits')).filter(num_exits__gt=0)
    if tot_enter_events.exists():
        b = tot_enter_events.annotate(
            early_exits=Min('exits__timestamp'),
            timediff=ExpressionWrapper(F('early_exits') - F('timestamp'),
                                       output_field=DurationField())
        ).aggregate(sum_diff=Sum('timediff'))

        sum_diff = b['sum_diff']

        return sum_diff.total_seconds()
    # TODO: ====================
    else:
        params = {'player_id': player.pk, 'participant': player.participant, 'page_name': page_name}
        if Marker.objects.filter(**params).exists():
            m = Marker.objects.get(**params)
            now = timezone.now()
            diff = now - m.timestamp
            return diff.total_seconds()
        else:
            if none_to_zero:
                return 0
            else:
                return None
    # TODO: ====================


def _aggregate_focus_time(player, page_name, focus_on=True):
    relfocuses = FocusEvent.objects.filter(player_id=player.pk, participant=player.participant,
                                           page_name=page_name).order_by('-timestamp')
    if not relfocuses.exists():
        return

    exit_types = [1, 2, 5]
    enter_types = [0, 3, 4]
    if relfocuses.first().event_num_type not in exit_types:
        return
    if relfocuses.last().event_num_type not in enter_types:
        return
    for i in relfocuses:
        if i.event_num_type in exit_types:
            i.general_type = 0
        else:
            i.general_type = 1

    tot_focus_on = tot_focus_off = timedelta()

    for index, obj in enumerate(relfocuses):
        if index > 0:
            previous = relfocuses[index - 1]
            if obj.general_type != previous.general_type:
                if obj.general_type == 1:
                    tot_focus_on += (previous.timestamp - obj.timestamp)
                else:
                    tot_focus_off += (previous.timestamp - obj.timestamp)
    if focus_on:
        return tot_focus_on.total_seconds()
    else:
        return tot_focus_off.total_seconds()


def get_focused_time(player, page_name):
    return _aggregate_focus_time(player, page_name)


def get_unfocused_time(player, page_name):
    return _aggregate_focus_time(player, page_name, focus_on=False)


def _get_numbers(player, page_name, event_type):
    return FocusEvent.objects.filter(player_id=player.pk, participant=player.participant,
                                     page_name=page_name, event_num_type=event_type).count()


def num_focus_events(player, page_name, off=True):
    if off:
        return _get_numbers(player, page_name, 2)
    else:
        return _get_numbers(player, page_name, 4)


def num_visibility_events(player, page_name, off=True):
    if off:
        return _get_numbers(player, page_name, 1)
    else:
        return _get_numbers(player, page_name, 3)
