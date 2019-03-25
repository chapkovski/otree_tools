import vanilla
import csv
import os
import json
from datetime import datetime

from django.db.models import ExpressionWrapper, F, DurationField
from django.views.generic import ListView, TemplateView, View
from django.http import HttpResponse
from django.core.urlresolvers import reverse

from otree.models import Session, Participant
from otree.views.export import get_export_response

from .models import Exit, FocusEvent, allowed_export_tracker_requests
from .export import export_wide
from . import __version__ as otree_tools_version


# TIME STAMPS VIEWS FOR TRACKING_TIME and TRACKING_FOCUS
class EnterExitMixin:
    def get_queryset(self):
        # TODO: group by page name?
        tot_exits = Exit.objects.filter(
            enter__isnull=False,
        ).annotate(diff=ExpressionWrapper(F('timestamp') - F('enter__timestamp'),
                                          output_field=DurationField()))
        for i in tot_exits:
            if i.diff is None:
                i.diff = i.timestamp - i.enter.timestamp
        return tot_exits


class PaginatedListView(ListView):
    navbar_active_tag = None
    export_link_name = None

    def get_context_data(self, **kwargs):
        c = super().get_context_data(**kwargs)
        c['nbar'] = self.navbar_active_tag
        curpage_num = c['page_obj'].number
        paginator = c['paginator']
        epsilon = 3
        c['allowed_range'] = range(max(1, curpage_num - epsilon), min(curpage_num + epsilon, paginator.num_pages) + 1)
        if self.export_link_name:
            c['export_link'] = reverse(self.export_link_name)
        return c


class EnterExitEventList(EnterExitMixin, PaginatedListView):
    template_name = 'otree_tools/trackers_export/all_timespent_list.html'
    url_name = 'time_spent_timestamps'
    url_pattern = r'^time_spent_per_page/$'
    display_name = 'Time spent per page [otree-tools]'
    context_object_name = 'timestamps'
    paginate_by = 50
    navbar_active_tag = 'time'


class TempFileCSVExport(View):
    """Receives a temp file name prepared in consumers, and returns it to a user.
    That is mostly for dealing with large files that can provoke server timeout errors."""
    url_name = 'export_tracker_data'
    url_pattern = fr'^export_tracker_data/(?P<tracker_type>{allowed_export_tracker_requests})/(?P<temp_file_name>.*)/$'
    content_type = 'text/csv'

    def get(self, request, *args, **kwargs):
        file_path = kwargs.get('temp_file_name')
        tracker_type = kwargs.get('tracker_type')
        curtime = datetime.now().strftime("%d_%m_%Y__%H_%M_%S")
        filename = f'{tracker_type}_{curtime}.csv'

        fsock = open(file_path, "r")
        response = HttpResponse(fsock, content_type=self.content_type)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        fsock.close()
        try:
            os.remove(file_path)
        except FileNotFoundError:
            pass
            # TODO logger.warning('temp file not found')
        return response


########### BLOCK: FOCUS EVENTS EXPORT BLOCK ##############################################################

class FocusPerPageReport(PaginatedListView):
    template_name = 'otree_tools/trackers_export/focus_per_page_report.html'
    url_name = 'focus_per_page_report'
    url_pattern = r'^focus_per_page_report/$'
    display_name = 'Focused/unfocused [otree-tools]'
    context_object_name = 'focusevents'
    paginate_by = 50
    navbar_active_tag = 'focus'


    def get_queryset(self):
        return FocusEvent.objects.get_per_page_report()


class FocusEventList(PaginatedListView):
    template_name = 'otree_tools/trackers_export/focus_event_list.html'
    url_name = 'focus_events'
    url_pattern = r'^focus_events/$'
    display_name = 'Focus/unfocus events [otree-tools]'
    context_object_name = 'focusevents'
    queryset = FocusEvent.objects.all()
    paginate_by = 50
    navbar_active_tag = 'focus'


############ END OF: FOCUS EVENTS EXPORT BLOCK #############################################################


# END OF TIME STAMPS BLOCK


# Welcoming page
class HomeView(TemplateView):
    template_name = 'otree_tools/home.html'
    url_name = 'otree_tools_home'
    url_pattern = r'^otree_tools/$'
    display_name = 'otree-tools Home page'
    navbar_active_tag = 'home'

    def get_context_data(self, **kwargs):
        c = super().get_context_data(**kwargs)
        c['nbar'] = self.navbar_active_tag
        c['version'] = otree_tools_version
        return c


########### BLOCK: EXPORTING PARTICIPANT.VARS MODULE ##############################################################


class UniversalEncoder(json.JSONEncoder):
    """A 'universal encoder for exporting participant.vars."""

    def default(self, obj):
        if isinstance(obj, (set, range)):
            return list(obj)
        try:
            return json.JSONEncoder.default(self, obj)
        except TypeError:
            try:
                return str(obj)
            # the last resort - if built-in __str__ of the object causes an error we fail silently
            except:
                return ''


class PVarsMixin(object):
    """Mixin to use for exporting participant.vars both for text and html."""

    def get_session(self):
        return Session.objects.get(pk=self.kwargs.get('pk'))

    def get_queryset(self):
        headers_to_add = ['session.code', 'player.code']
        session = self.get_session()
        data = Participant.objects.filter(session=session).values('vars', 'code', 'session__code')
        # todo: sort the headers
        keys = sorted(list(set().union(*(d['vars'].keys() for d in data))), key=lambda s: s.lower())
        self.heads = headers_to_add + keys
        q = list()
        for i in data:
            dict_to_row = json.loads(json.dumps(i['vars'], cls=UniversalEncoder))
            row = [i['session__code'], i['code']] + [dict_to_row.get(key, '') for key in keys]
            q.append(row)

        return q


class ListPVarsView(PVarsMixin, PaginatedListView):
    """Returns  all participant vars in the database - per session."""
    template_name = 'otree_tools/pvars_list.html'
    url_name = 'pvars_list'
    url_pattern = r'^session/(?P<pk>[a-zA-Z0-9_-]+)/pvars/$'
    model = Participant
    context_object_name = 'pvars'
    paginate_by = 20
    navbar_active_tag = 'export'
    export_link_name = None

    def get_context_data(self, **kwargs):
        c = super().get_context_data(**kwargs)
        session = self.get_session()
        c['session'] = session
        c['heads'] = self.heads
        c['export_link'] = reverse('pvars_csv_export', kwargs={'pk': session.pk})
        return c


class PVarsCSVExport(PVarsMixin, TemplateView):
    """Returns the textual file   all participant vars in the database - per session."""
    url_name = 'pvars_csv_export'
    url_pattern = r'^session/(?P<pk>[a-zA-Z0-9_-]+)/pvars_csv_export/$'
    response_class = HttpResponse
    content_type = 'text/csv'

    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type='text/csv')
        session_code = self.get_session().code
        filename = f'{session_code}_participant_vars.csv'
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)

        pvars = self.get_queryset()
        writer = csv.writer(response)
        writer.writerow(self.heads)

        for p in pvars:
            writer.writerow(p)

        return response


############ END OF: EXPORTING PARTICIPANT.VARS MODULE #############################################################


########### BLOCK: SPECIFIC SESSION EXPORT ##############################################################


class AllSessionsList(PaginatedListView):
    template_name = 'otree_tools/all_session_list.html'
    url_name = 'individual_sessions_export'
    url_pattern = r'^individual_sessions_export/$'
    display_name = 'Exporting data from individual sessions'
    navbar_active_tag = 'export'
    queryset = Session.objects.all()
    context_object_name = 'sessions'
    paginate_by = 10


class SpecificSessionDataView(vanilla.TemplateView):
    url_pattern = r'^session_data/(?P<session_code>.*)/(?P<filetype>.*)/$'
    url_name = 'session_data'

    def get(self, request, *args, **kwargs):
        session_code = kwargs['session_code']
        response, file_extension = get_export_response(
            request, session_code)
        export_wide(response, file_extension, session_code=session_code)
        return response

############ END OF: SPECIFIC SESSION EXPORT #############################################################
