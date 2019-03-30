import json
from datetime import datetime
from otree_tools.models import (Enter, Exit, FocusEvent)
from otree_tools.constants import *
from channels.generic.websockets import JsonWebsocketConsumer
from django.contrib.contenttypes.models import ContentType
from otree.models import Participant
from otree.models_concrete import ParticipantToPlayerLookup
import logging
from otree_tools import cp
from otree_tools.prepare_export_data import FileMaker
from django.db import IntegrityError, transaction
from django.template.loader import render_to_string

logger = logging.getLogger('otree_tools.consumers')

"""
Export of timing objects is relatively slow thing.
We should check whether redis is available - if yes, we can try to use hyeu to create a task that will call
initiate downloading as soon as the file is ready.

An alternative solution would be to send a signal to database, and start preparing file. 
as soon as it is ready the signal is sent back, which allows to download it.
A
"""


class GeneralTracker(JsonWebsocketConsumer):
    tracker_url_kwargs = r'(?P<participant_code>[a-zA-Z0-9_-]+)/(?P<page_name>[a-zA-Z0-9_-]+)/(?P<page_index>\d+)$'

    def clean_kwargs(self):
        self.participant_code = self.kwargs['participant_code']
        self.page_name = self.kwargs['page_name']
        self.page_index = self.kwargs['page_index']

    def get_participant(self):
        self.clean_kwargs()
        try:
            return Participant.objects.get(code__exact=self.participant_code)
        except Participant.DoesNotExist:
            return

    def get_player_and_app(self):
        empty_ret = (None, None, None)
        participant = self.get_participant()
        if participant:
            try:
                participant_lookup_item = participant.participanttoplayerlookup_set.get(
                    page_index=self.page_index)
                app_name = participant_lookup_item.app_name
                player_pk = participant_lookup_item.player_pk

                player_content_type = ContentType.objects.get(app_label=app_name, model='player')
                player = player_content_type.get_object_for_this_type(pk=player_pk)
                return participant, app_name, player

            except ParticipantToPlayerLookup.DoesNotExist:
                logger.error('Cannot find participant for this page!')
        return empty_ret


class TimeTracker(GeneralTracker):
    url_pattern = (r'^/timetracker/' + GeneralTracker.tracker_url_kwargs)

    def create_event(self, timestamp, event_type, exit_type=None, wait_for_images=False):
        """Register new enter or exit event based on incoming data."""
        participant, app_name, player = self.get_player_and_app()
        filter_params = {'page_name': self.page_name,
                         'participant': participant,
                         'app_name': app_name, }
        general_params = {**filter_params,
                          'player': player,
                          'timestamp': timestamp,
                          'round_number': player.round_number}
        if event_type == 'enter':
            if participant is not None:
                Enter.objects.create(**general_params,
                                     wait_for_images=wait_for_images)
        if event_type == 'exit':
            if participant is not None:
                most_recent_exits = Exit.objects.filter(**filter_params)
                if most_recent_exits.exists():
                    last_exit_time = most_recent_exits.latest('timestamp').timestamp
                    filter_params['timestamp__gt'] = last_exit_time
                try:
                    enter = Enter.objects.filter(**filter_params,
                                                 timestamp__lte=timestamp,
                                                 player_id=player.pk,
                                                 exit__isnull=True).latest('timestamp')
                except Enter.DoesNotExist:
                    enter = None
                try:
                    with transaction.atomic():
                        Exit.objects.create(**general_params,
                                            exit_type=exit_type,
                                            enter=enter
                                            )
                except IntegrityError:
                    # This may happen despite some efforts above because of concurrency.
                    enter = None
                    Exit.objects.create(**general_params,
                                        exit_type=exit_type,
                                        enter=enter
                                        )

    def receive(self, content, **kwargs):
        """We get some data (timestamp, event type) from user and register them in db"""
        raw_content = json.loads(content)
        raw_time = raw_content['timestamp']
        timestamp = datetime.fromtimestamp(raw_time / 1000)
        event_type = raw_content['eventtype']
        wait_for_images = raw_content.get('wait_for_images', True)
        self.create_event(timestamp, event_type, wait_for_images)

    def connect(self, message, **kwargs):
        logger.info('Client connected to time tracker...')

    def disconnect(self, message, **kwargs):
        timestamp = datetime.now()
        event_type = 'exit'
        self.create_event(timestamp, event_type, exit_type=ExitTypes.CLIENT_DISCONNECTED.value)
        logger.info('Client disconnected from time tracker...')


class FocusTracker(GeneralTracker):
    url_pattern = (r'^/focustracker/' + GeneralTracker.tracker_url_kwargs)

    def get_entry(self):
        filter_params = {**self.filter_params,
                         'timestamp__lte': self.timestamp,
                         'player_id': self.player.pk,
                         'closure__isnull': True
                         }
        if self.event_num_type in focus_enter_codes:
            filter_params['event_num_type__in'] = focus_exit_codes

        if self.event_num_type in focus_exit_codes:
            filter_params['event_num_type__in'] = focus_enter_codes
        entry = FocusEvent.objects.filter(**filter_params, )
        if entry.exists():
            entry = entry.latest('timestamp')
        else:
            entry = None
        return entry

    def receive(self, content, **kwargs):
        raw_content = json.loads(content)
        raw_time = raw_content['timestamp']
        self.timestamp = datetime.fromtimestamp(raw_time / 1000)
        self.event_num_type = raw_content['event_num_type']
        event_desc_type = raw_content['event_desc_type']
        participant, app_name, self.player = self.get_player_and_app()
        self.filter_params = {'page_name': self.page_name,
                              'participant': participant,
                              'app_name': app_name, }
        if participant is not None:
            entry = self.get_entry()
            creating_params = {**self.filter_params,
                               'timestamp': self.timestamp,
                               'player': self.player,
                               'round_number': self.player.round_number,
                               'event_desc_type': event_desc_type,
                               "event_num_type": self.event_num_type,
                               "entry": entry}
            try:
                FocusEvent.objects.create(**creating_params)
            except IntegrityError:
                creating_params['entry'] = None
                FocusEvent.objects.create(**creating_params)

    def connect(self, message, **kwargs):
        # todo add enter event
        print('Client connected to focus tracker...')


class ExportTracker(JsonWebsocketConsumer):
    url_pattern = r'^/exporttracker/(?P<inner_group_id>.*)$'
    progress_block_name = 'otree_tools/includes/progress_block.html'

    def connection_groups(self, **kwargs):
        return [self.kwargs['inner_group_id']]

    def receive(self, content, **kwargs):
        raw_content = json.loads(content)
        request = raw_content['request']
        tracker_type = raw_content['tracker_type']

        if request == 'export':
            msg = {'button': render_to_string(self.progress_block_name, {})}
            self.send(msg)
            file_maker = FileMaker(channel_to_response=self.kwargs['inner_group_id'],
                                   tracker_type=tracker_type)
            file_maker.get_data()

    def connect(self, message, **kwargs):
        logger.info('Client connected to export tracker...')

    def disconnect(self, message, **kwargs):
        logger.info('Client disconnected from export tracker...')
#
