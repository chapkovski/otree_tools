from django.db import models
from otree.models import Participant
from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from otree_tools import cp
from django.db.models import F, ExpressionWrapper, DurationField, Sum, Min, Case, When, Count, FloatField, \
    IntegerField
from django.db.models.functions import Cast
from datetime import timedelta
from otree_tools.constants import *

allowed_export_tracker_requests = r'(time|focus_per_page|focus_raw)'


class GeneralEvent(models.Model):
    class Meta:
        get_latest_by = 'timestamp'
        abstract = True

    page_name = models.CharField(max_length=1000)
    participant = models.ForeignKey(to=Participant, related_name="%(app_label)s_%(class)s_events")
    app_name = models.CharField(max_length=1000)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    player_id = models.PositiveIntegerField()
    player = GenericForeignKey('content_type', 'player_id')
    timestamp = models.DateTimeField()
    round_number = models.PositiveIntegerField()


class Enter(GeneralEvent):
    wait_for_images = models.BooleanField(choices=WAITFORIMAGES_CHOICES, default=True)

    def __str__(self):
        return f'id: {self.pk}, Enter: {self.page_name}; time: {self.timestamp}'


class ExitExportManager(models.Manager):
    """Manager for correctly exporting data to templates and csv from time trackers."""

    def time(self):
        tot_exits = super().get_queryset().filter(enter__isnull=False, ). \
            values('participant',
                   'app_name',
                   'page_name',
                   'player_id',
                   'participant__code',
                   'participant__session__code',
                   'round_number',
                   ). \
            annotate(diff=Sum(ExpressionWrapper(F('timestamp') - F('enter__timestamp'),
                                                output_field=DurationField())),
                     timestamp=F('timestamp'),
                     enter_timestamp=F('enter__timestamp'),
                     exit_type=F('exit_type'),
                     wait_for_images=F('enter__wait_for_images'))
        return tot_exits


class Exit(GeneralEvent):
    objects = models.Manager()
    export = ExitExportManager()
    enter = models.OneToOneField(to='Enter', related_name='exit', null=True)
    timestamp = models.DateTimeField()
    exit_type = models.IntegerField(choices=EXITTYPES)

    def __str__(self):
        return f'id: {self.pk}, Exit: {self.page_name}; time: {self.timestamp}; Type: {self.get_exit_type_display()} '


class FocusExportManager(models.Manager):
    def focus_per_page(self):
        return self.model.objects.get_per_page_report()

    def focus_raw(self):
        return super().get_queryset()


class FocusManager(models.Manager):
    def _get_tracked_time(self, player_id, participant_id, page_name, focus_type):
        tot_exits = super().get_queryset().values('participant',
                                                  'page_name',
                                                  'player_id'). \
            filter(player_id=player_id,
                   participant_id=participant_id,
                   page_name=page_name,
                   entry__isnull=False,
                   ). \
            aggregate(
            diff=Sum(Case(
                When(event_num_type__in=focus_type,
                     then=ExpressionWrapper(F('timestamp') - F('entry__timestamp'),
                                            output_field=DurationField())),
                output_field=DurationField(),
            )),
            num_unfocus=Count(Case(
                When(event_num_type=2, then=1),
                output_field=IntegerField(),
            ))
            # num_unfocus=Count(
            #     Case(When(event_num_type=FocusExitEventTypes.FOCUS_OFF, then=1), output_field=IntegerField()))
        )

        return tot_exits

    def get_focused_time_per_page(self, player_id, participant_id, page_name):
        diff = self._get_tracked_time(player_id, participant_id, page_name, focus_exit_codes)['diff'] or timedelta()
        return diff.total_seconds()

    def get_unfocused_time_per_page(self, player_id, participant_id, page_name):
        diff = self._get_tracked_time(player_id, participant_id, page_name, focus_enter_codes)['diff'] or timedelta()
        return diff.total_seconds()

    def num_focusoff_events(self, player_id, participant_id, page_name):
        num_unfocus = self._get_tracked_time(player_id, participant_id, page_name, focus_exit_codes)['num_unfocus']
        return num_unfocus

    def get_per_page_report(self):
        q = super().get_queryset().values('participant',
                                          'app_name',
                                          'page_name',
                                          'player_id',
                                          'participant__code',
                                          'participant__session__code',
                                          'round_number'). \
            filter(entry__isnull=False). \
            annotate(
            focused_time=Sum(Case(
                When(event_num_type__in=focus_exit_codes,
                     then=ExpressionWrapper(F('timestamp') - F('entry__timestamp'),
                                            output_field=DurationField())),
                output_field=DurationField(),
            )),
            unfocused_time=Sum(Case(
                When(event_num_type__in=focus_enter_codes,
                     then=ExpressionWrapper(F('timestamp') - F('entry__timestamp'),
                                            output_field=DurationField())),
                output_field=DurationField(),
            )),
            num_unfocus=Count(
                Case(When(event_num_type=FocusExitEventTypes.FOCUS_OFF.value, then=1), output_field=IntegerField())),
        ).annotate(total_time=Sum(ExpressionWrapper(F('timestamp') - F('entry__timestamp'),
                                                    output_field=DurationField())))

        return q


class FocusEvent(GeneralEvent):
    objects = FocusManager()
    export = FocusExportManager()
    event_desc_type = models.CharField(max_length=1000)
    event_num_type = models.IntegerField(choices=FOCUS_EVENT_TYPES)
    # we track focus events that have corresponding closuring focus event to
    # correctly calculate focus on/focus off time
    entry = models.OneToOneField(to='FocusEvent',
                                 related_name='closure',
                                 null=True,
                                 )

    def __str__(self):
        return f'id: {self.pk}, event_desc_type: {self.event_desc_type}; time: {self.timestamp};'
