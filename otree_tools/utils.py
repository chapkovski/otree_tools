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
from django.db.models import OuterRef, Subquery, ExpressionWrapper, F, DateTimeField, DurationField, IntegerField, \
    FloatField
from datetime import datetime, timedelta
from django.db.models.functions import Cast
from django.db.models import Value, Count, Max, Min, Sum


def get_time_per_page(player, page_name):
    tot_enter_events = EnterEvent.objects.filter(participant=player.participant,
                                                 page_name=page_name
                                                 ).annotate(num_exits=Count('exits')).filter(num_exits__gt=0)
    if tot_enter_events.exists():
        b = tot_enter_events.annotate(
            early_exits=Min('exits__timestamp'),
            timediff=ExpressionWrapper(F('early_exits') - F('timestamp'),
                                       output_field=DurationField())
        ).aggregate(sum_diff=Sum('timediff'))

        sum_diff = b['sum_diff']

        return sum_diff
