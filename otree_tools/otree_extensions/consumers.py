from channels.generic.websockets import JsonWebsocketConsumer
from otree.models import Participant
from datetime import datetime
from otree_tools.models import EnterEvent, ExitEvent
import json
import time


class TimeTracker(JsonWebsocketConsumer):
    url_pattern = (r'^/timetracker/(?P<participant_code>[a-zA-Z0-9_-]+)$')

    def clean_kwargs(self):
        self.participant_code = self.kwargs['participant_code']

    def get_unclosed_enter_event(self):
        o = EnterEvent.opened.all()
        if o.exists():
            return o.latest()

    def receive(self, content, **kwargs):
        raw_content = json.loads(content)
        raw_time = raw_content['timestamp']
        exit_time = datetime.fromtimestamp(raw_time / 1000)
        # TODO: can other than exit events be sent to this channel as messages? Then we have to check for that
        exit_type = int(raw_content['eventtype'])
        # TODO: the right way of doing things is to move all event registration here from connect (and leave some pieces
        #     in disconnected
        latest_entry = self.get_unclosed_enter_event()
        if latest_entry is not None:
            latest_entry.exits.create(timestamp=exit_time,
                                      exit_type=exit_type)

    def get_participant(self):
        self.clean_kwargs()
        return Participant.objects.get(code__exact=self.participant_code)

    def connect(self, message, **kwargs):
        participant = self.get_participant()
        EnterEvent.opened.close_all(participant)
        # TODO: record actual passed time onopen, not datetime.now()
        participant.enters.create(page_name=participant._current_page_name,
                                  timestamp=datetime.now())

    def disconnect(self, message, **kwargs):
        print('DISCONNECTING)')
        participant = self.get_participant()
        latest_entry = self.get_unclosed_enter_event()
        if latest_entry is not None:
            latest_entry.exits.create(timestamp=datetime.now(),
                                      exit_type=2)

            EnterEvent.opened.close_all(participant)
