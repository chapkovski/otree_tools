import json
from datetime import datetime

from channels.generic.websockets import JsonWebsocketConsumer
from django.contrib.contenttypes.models import ContentType
from otree.models import Participant
from otree_tools.models import EnterEvent


class TimeTracker(JsonWebsocketConsumer):
    url_pattern = (r'^/timetracker/(?P<participant_code>[a-zA-Z0-9_-]+)/(?P<page_name>[a-zA-Z0-9_-]+)$')

    def clean_kwargs(self):
        self.participant_code = self.kwargs['participant_code']
        self.page_name = self.kwargs['page_name']

    def get_unclosed_enter_event(self):
        o = EnterEvent.opened.all()
        if o.exists():
            return o.latest()

    def receive(self, content, **kwargs):
        raw_content = json.loads(content)
        raw_time = raw_content['timestamp']
        timestamp = datetime.fromtimestamp(raw_time / 1000)
        eventtype = raw_content['eventtype']
        if eventtype == 'enter':
            participant = self.get_participant()
            participant_lookup_item = participant.participanttoplayerlookup_set.get(
                page_index=participant._index_in_pages)
            app_name = participant_lookup_item.app_name
            player_pk = participant_lookup_item.player_pk

            player_content_type = ContentType.objects.get(app_label=app_name, model='player')
            player = player_content_type.get_object_for_this_type(pk=player_pk)
            EnterEvent.opened.close_all(participant, self.page_name, )

            participant.enters.create(page_name=self.page_name,
                                      timestamp=timestamp,
                                      player=player,
                                      app_name=app_name)
        if eventtype == 'exit':
            exit_type = int(raw_content['exittype'])
            latest_entry = self.get_unclosed_enter_event()
            if latest_entry is not None:
                latest_entry.exits.create(timestamp=timestamp,
                                          exit_type=exit_type)

    def get_participant(self):
        self.clean_kwargs()
        return Participant.objects.get(code__exact=self.participant_code)

    def connect(self, message, **kwargs):
        print('Client connected to time tracker...')

    def disconnect(self, message, **kwargs):
        participant = self.get_participant()
        latest_entry = self.get_unclosed_enter_event()
        if latest_entry is not None:
            latest_entry.exits.create(timestamp=datetime.now(),
                                      exit_type=2)

            EnterEvent.opened.close_all(participant, self.page_name)
