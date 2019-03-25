from otree.models import Session
from django.views.generic import TemplateView, View
from django.shortcuts import render
from .serializers import SessionSerializer
from rest_framework import generics
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
import random
import string
import os
from django.http import HttpResponse
from wsgiref.util import FileWrapper


def get_full_file_name(filename):
    return 'serializer_ext/temp/{}'.format(filename)


def get_random_code():
    return ''.join(random.choice(string.ascii_letters) for i in range(10))


def get_file_name(session_code, random_code):
    return 'session_data_{}_{}.json'.format(session_code, random_code)


def downloadable_filename(session_code):
    return 'session_data_{}.json'.format(session_code)


# TODO: move up imports
import json
from django.template import Context, loader


class DownloadJson(TemplateView):
    template_name = 'download_json.json'
    url_pattern = r'^download_json/(?P<session_code>\w+)$'
    url_name = 'download_json'

    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type='application/json')
        session_code = self.kwargs['session_code']
        filename = '{}_json_data.json'.format(session_code)
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)
        session = Session.objects.filter(code=session_code)
        result = SessionSerializer(session, many=True, )
        data = json.dumps(result.data, indent=4)
        t = loader.get_template(self.template_name)
        c = {
            'data': data,
        }
        response.write(t.render(c))
        return response


# the view to get a list of all sessions
class AllSessionsList(TemplateView):
    template_name = 'serializer_ext/all_session_list.html'
    url_name = 'json_sessions_list'
    url_pattern = r'^sessions_list_for_json/$'
    display_name = 'Exporting data to JSON'

    def get(self, request, *args, **kwargs):
        all_sessions = Session.objects.all()
        return render(request, self.template_name, {'sessions': all_sessions})
