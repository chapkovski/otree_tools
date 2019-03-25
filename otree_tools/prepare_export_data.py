from otree_tools.models import Exit, FocusEvent
import tempfile
from django.urls import reverse
from django.template.loader import render_to_string
from channels import Group as ChannelGroup
import json

export_tracker_correspondence = {'time': {'model': Exit, 'method': 'all'},
                                 'focus_raw': {'model': FocusEvent, 'method': 'raw'},
                                 'focus_per_page': {'model': FocusEvent, 'method': 'per_page'},
                                 }


class FileMaker:
    button_block = 'otree_tools/includes/initial_export_button.html'

    def __init__(self, channel_to_response, tracker_type):
        self.channel_to_response = channel_to_response
        self.tracker_type = tracker_type
        self.template_name = f'otree_tools/trackers_export/{tracker_type}_data.csv'

    def get_data(self):
        model = export_tracker_correspondence[tracker_type]['model']
        c = {
            'events': csv_data,
        }

        fp = tempfile.NamedTemporaryFile(
            'w', prefix=f'{self.tracker_type}_', suffix='.csv', encoding='utf-8', delete=False)
        fp.write(render_to_string(self.template_name, c))
        fp.flush()
        link_to_send = reverse('export_time', kwargs={'temp_file_name': fp.name,
                                                      'tracker_type': self.tracker_type})
        channel = ChannelGroup(channel_to_response)
        channel.send({'text': json.dumps({'url': link_to_send,
                                          'button': render_to_string(self.button_block)})
                      })


class TimeFileMaker(FileMaker):
    model = Exit


class FocusRawFileMaker(FileMaker):
    model  = FocusEvent


class FocusPerPageFileMaker(FileMaker):
    model = FocusEvent
