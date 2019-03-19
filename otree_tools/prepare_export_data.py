from otree_tools.models import Exit
import tempfile
from django.urls import reverse
from django.template.loader import render_to_string
from channels import Group as ChannelGroup
import json
from django.db.models import DurationField, ExpressionWrapper, F


def make_file(channel_to_response):
    csv_data = Exit.objects.filter(
        enter__isnull=False,
    ).annotate(diff=ExpressionWrapper(F('timestamp') - F('enter__timestamp'),
                                      output_field=DurationField()))
    for i in csv_data:
        if i.diff is None:
            i.diff = i.timestamp - i.enter.timestamp
    template_name = 'otree_tools/enter_exit_data.csv'
    button_block = 'otree_tools/includes/initial_export_button.html'
    c = {
        'events': csv_data,
    }

    fp = tempfile.NamedTemporaryFile(
        'w', prefix='time_events_', suffix='.csv', encoding='utf-8', delete=False)
    fp.write(render_to_string(template_name, c))
    fp.flush()
    link_to_send = reverse('export_time', kwargs={'innerurl': fp.name})
    channel = ChannelGroup(channel_to_response)
    channel.send({'text': json.dumps({'url': link_to_send,
                                      'button': render_to_string(button_block)})
                  })
