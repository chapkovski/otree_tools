from channels.generic.websockets import JsonWebsocketConsumer
from otree_tools.models import TimeStamp
from otree.models import Participant


class TimeTracker(JsonWebsocketConsumer):
    url_pattern = (r'^/timetracker/(?P<participant_code>[a-zA-Z0-9_-]+)$')

    def clean_kwargs(self):
        self.participant_code = self.kwargs['participant_code']


    def get_participant(self):
        self.clean_kwargs()
        return Participant.objects.get(code__exact=self.participant_code)


    def connect(self, message, **kwargs):
        participant = self.get_participant()
        print('IM CONNECTED')
        # unanswered_tasks = player.get_unfinished_tasks()
        # if unanswered_tasks.exists():
        #     task = unanswered_tasks.first()
        # else:
        #     task = player.tasks.create()
        # response = self.prepare_task(player, task)
        # self.send(response)
        #
    def disconnect(self, message, **kwargs):
        print('IM DISCONNECTED')
