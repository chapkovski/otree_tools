from otree.models_concrete import PageCompletion


def get_seconds_per_page(player, page_name):
    participant = player.participant
    subsession_pk = player.subsession.pk
    try:
        page_info = PageCompletion.objects.get(participant=participant, subsession_pk=subsession_pk,
                                               page_name=page_name)
    except PageCompletion.DoesNotExist:
        raise ValueError('Cannot find info about this page')
    return page_info.seconds_on_page


from otree_tools.models import EnterEvent, ExitEvent
from django.db.models import OuterRef, Subquery
from datetime import datetime, timedelta


def get_time_per_page(player, page_name):
    earliest = ExitEvent.objects.filter(enter_event=OuterRef('pk')).order_by('timestamp')
    delta = timedelta(days=1)

    a = EnterEvent.objects.filter(closed=True,
                                  participant=player.participant,
                                  page_name=page_name).annotate(
        earliest_exit=Subquery(earliest.values('timestamp')[:1]),
    ).values()
    sum_diff = sum([i['earliest_exit'] - i['timestamp'] for i in a], timedelta())

    return sum_diff
