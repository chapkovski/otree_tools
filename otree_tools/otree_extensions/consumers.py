import json
from datetime import datetime
from otree_tools.models import Enter, Exit
from channels.generic.websockets import JsonWebsocketConsumer
from django.contrib.contenttypes.models import ContentType
from otree.models import Participant
from otree.models_concrete import ParticipantToPlayerLookup
import logging
from utils import cp
from otree_tools.prepare_export_data import make_file
from django.db.utils import IntegrityError
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
    # TODO: deal with page unloaded registered BEFORE form submitted
    url_pattern = (r'^/timetracker/' + GeneralTracker.tracker_url_kwargs)

    def receive(self, content, **kwargs):
        raw_content = json.loads(content)
        raw_time = raw_content['timestamp']
        timestamp = datetime.fromtimestamp(raw_time / 1000)
        event_type = raw_content['eventtype']
        wait_for_images = raw_content.get('wait_for_images', True)
        participant, app_name, player = self.get_player_and_app()
        filter_params = {'page_name': self.page_name,
                         'participant': participant,
                         'app_name': app_name, }
        general_params = {**filter_params,
                          'player': player,
                          'timestamp': timestamp}
        if event_type == 'enter':
            if participant is not None:
                Enter.objects.create(**general_params,
                                     wait_for_images=wait_for_images)

        if event_type == 'exit':
            if participant is not None:
                exit_type = int(raw_content['exittype'])
                try:
                    enter = Enter.objects.filter(**filter_params,
                                                 timestamp__lte=timestamp,
                                                 player_id=player.pk,
                                                 exit__isnull=True).latest()
                except Enter.DoesNotExist:
                    enter = None

                try:
                    e = Exit(**general_params,
                             exit_type=exit_type,
                             enter=enter
                             )
                    e.save()
                except IntegrityError:
                    enter = None
                    e = Exit(**general_params,
                             exit_type=exit_type,
                             enter=enter
                             )
                    e.save()

    def connect(self, message, **kwargs):
        print('Client connected to time tracker...')

    def disconnect(self, message, **kwargs):
        print('Client disconnected from time tracker...')


#

class FocusTracker(GeneralTracker):
    url_pattern = (r'^/focustracker/' + GeneralTracker.tracker_url_kwargs)

    def receive(self, content, **kwargs):
        raw_content = json.loads(content)
        raw_time = raw_content['timestamp']
        timestamp = datetime.fromtimestamp(raw_time / 1000)
        event_num_type = raw_content['event_num_type']
        event_desc_type = raw_content['event_desc_type']

        participant, app_name, player = self.get_player_and_app()
        if participant is not None:
            participant.otree_tools_focusevent_events.create(page_name=self.page_name,
                                                             timestamp=timestamp,
                                                             player=player,
                                                             app_name=app_name,
                                                             event_desc_type=event_desc_type,
                                                             event_num_type=event_num_type, )

    def connect(self, message, **kwargs):
        print('Client connected to focus tracker...')


class ExportTracker(JsonWebsocketConsumer):
    url_pattern = (r'^/exporttracker/(?P<inner_group_id>.*)$')
    progress_block_name = 'tester/includes/progress_block.html'

    def connection_groups(self, **kwargs):
        return [self.kwargs['inner_group_id']]

    def receive(self, content, **kwargs):
        raw_content = json.loads(content)
        request = raw_content['request']
        if request == 'export':
            msg = {'button': render_to_string(self.progress_block_name, {})}
            self.send(msg)
            make_file(channel_to_response=self.kwargs['inner_group_id'])

    def connect(self, message, **kwargs):
        print('Client connected to export tracker...')

    def disconnect(self, message, **kwargs):
        print('Client disconnected from export tracker...')
#
