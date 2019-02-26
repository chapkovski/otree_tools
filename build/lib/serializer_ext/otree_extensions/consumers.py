from channels.generic.websockets import WebsocketConsumer
import json
from otree.models import Session
from serializer_ext.serializers import SessionSerializer
from rest_framework import generics
from django.urls import reverse
from serializer_ext.views import get_full_file_name, get_file_name, get_random_code


class JsonLoader(WebsocketConsumer):
    url_pattern = (
        r'^/jsonloader/$')
        # '/session/(?P<session_code>[a-zA-Z0-9_-]+)' +
        # '$')

    def clean_kwargs(self, kwargs):
        self.session = self.kwargs['session_code']

    def receive(self, text=None, bytes=None, **kwargs):
        json_data = json.loads(text)
        session_code =json_data.get('session_code')
        if session_code:
            session = Session.objects.filter(code=session_code)
            result = SessionSerializer(session, many=True, )
            random_code = get_random_code()
            filename = get_file_name(session_code, random_code)
            with open(get_full_file_name(filename), "w+") as f:
                f.write(json.dumps(result.data, indent=4))
                download_link = reverse('download_json', kwargs={'session_code': session_code,
                                                                 'random_code': random_code})
            self.send({'file_ready': True,
                       'download_link': download_link,
                       'session_code': session_code})


    def connect(self, message, **kwargs):
        ...
        # print('Someone connected')


    def send(self, content):
        self.message.reply_channel.send({'text': json.dumps(content)})
