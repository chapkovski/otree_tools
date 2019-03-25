from otree_tools.models import Exit, FocusEvent
import tempfile
from django.urls import reverse
from django.template.loader import render_to_string
from channels import Group as ChannelGroup
import json
from otree_tools import cp
tracker_correspondence = {'time': Exit,
                          'focus_per_page': FocusEvent,
                          'focus_raw': FocusEvent}


class FileMaker:
    button_block = 'otree_tools/includes/initial_export_button.html'
    model = None

    def __init__(self, channel_to_response, tracker_type):
        self.model = tracker_correspondence[tracker_type]
        self.channel_to_response = channel_to_response
        self.tracker_type = tracker_type
        self.template_name = f'otree_tools/trackers_export/{tracker_type}_data.csv'
        self.channel = ChannelGroup(self.channel_to_response)

    def get_data(self):
        data_method = getattr(self.model.export, self.tracker_type)
        c = {
            'events': data_method(),
        }
        fp = tempfile.NamedTemporaryFile('w', prefix=f'{self.tracker_type}_',
                                         suffix='.csv',
                                         encoding='utf-8',
                                         delete=False)
        fp.write(render_to_string(self.template_name, c))
        fp.flush()
        link_to_send = reverse('export_tracker_data', kwargs={'temp_file_name': fp.name,
                                                              'tracker_type': self.tracker_type})

        self.channel.send({'text': json.dumps({'url': link_to_send,
                                               'button': render_to_string(self.button_block)})
                           })
