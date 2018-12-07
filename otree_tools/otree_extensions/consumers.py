import json
from datetime import datetime

from channels.generic.websockets import JsonWebsocketConsumer
from django.contrib.contenttypes.models import ContentType
from otree.models import Participant
from otree_tools.models import EnterEvent, FocusEvent, Marker
from otree.models_concrete import ParticipantToPlayerLookup
from django.utils import timezone


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
                ...
        return empty_ret


class TimeTracker(GeneralTracker):
    url_pattern = (r'^/timetracker/' + GeneralTracker.tracker_url_kwargs)

    def get_unclosed_enter_event(self):
        p = self.get_participant()
        o = EnterEvent.opened.filter(participant=p)
        if o.exists():
            return o.latest()

    def receive(self, content, **kwargs):
        raw_content = json.loads(content)
        raw_time = raw_content['timestamp']
        timestamp = datetime.fromtimestamp(raw_time / 1000)
        event_type = raw_content['eventtype']
        if event_type == 'enter':
            participant, app_name, player = self.get_player_and_app()
            if participant is not None:
                EnterEvent.opened.close_all(participant, self.page_name, )

                participant.otree_tools_enterevent_events.create(page_name=self.page_name,
                                                                 timestamp=timestamp,
                                                                 player=player,
                                                                 app_name=app_name)

        if event_type == 'exit':
            exit_type = int(raw_content['exittype'])
            latest_entry = self.get_unclosed_enter_event()
            if latest_entry is not None:
                latest_entry.exits.create(timestamp=timestamp,
                                          exit_type=exit_type)

    def connect(self, message, **kwargs):
        # TODO:===========
        participant, app_name, player = self.get_player_and_app()
        now = timezone.now()
        marker, created = Marker.objects.get_or_create(page_name=self.page_name,
                                                       participant=self.get_participant(),
                                                       player_id=player.id,
                                                       app_name=app_name,
                                                       defaults={'timestamp': now,
                                                                 'active': True,
                                                                 'player': player})
        # TODO:===========
        print('Client connected to time tracker...')

    def disconnect(self, message, **kwargs):
        participant = self.get_participant()
        latest_entry = self.get_unclosed_enter_event()
        # TODO:===========
        participant, app_name, player = self.get_player_and_app()
        now = timezone.now()
        params = {'page_name': self.page_name,
                  'participant': self.get_participant(),
                  'player_id': player.id,
                  'app_name': app_name, }
        markers= Marker.objects.filter(**params)
        if markers.exists():
            markers.update(active=False)
        # TODO:===========
        if latest_entry is not None:
            latest_entry.exits.create(timestamp=datetime.now(),
                                      exit_type=2)

            EnterEvent.opened.close_all(participant, self.page_name)


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
