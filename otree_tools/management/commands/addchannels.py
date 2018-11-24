from django.core.management.base import BaseCommand, CommandError
from otree_tools.utils import copy
import os
import otree_tools


class Command(BaseCommand):
    def get_channel_template(self):
        return os.path.join(
            os.path.dirname(otree_tools.__file__), 'channel_template')

    def add_arguments(self, parser):
        parser.add_argument('app_id', type=str)

    def handle(self, *args, **options):
        channels_js_folder = 'includes'
        extensions_folder = 'otree_extensions'
        app_id = options['app_id']
        path_to = self.get_channel_template()
        full_js_path = '{}/{}'.format(path_to, channels_js_folder)
        full_ext_path = '{}/{}'.format(path_to, extensions_folder)
        copy1 = copy(full_js_path, './{0}/templates/{0}/{1}'.format(app_id, channels_js_folder))
        copy2 = copy(full_ext_path, './{0}/{1}'.format(app_id, extensions_folder))
        if all([copy1, copy2]):
            self.stdout.write(self.style.SUCCESS('channels added to the app: "{}"'.format(app_id)))
            self.stdout.write(self.style.WARNING('Do not forget to add the following line into your settings.py:'))
            self.stdout.write(self.style.NOTICE('EXTENSION_APPS = "{}"'.format(app_id)))
            self.stdout.write(self.style.WARNING('and include the JavaScript template to your page template:'))
            self.stdout.write(self.style.NOTICE('{{% include "{}/includes/channel-js.html" %}}'.format(app_id)))
