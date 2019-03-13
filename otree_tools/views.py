import vanilla
# from botocore.exceptions import NoCredentialsError, EndpointConnectionError
from django.db.models import Count, Min, OuterRef, Subquery
from django.db.models import ExpressionWrapper, F, DurationField
from django.shortcuts import render
from django.views.generic import ListView, TemplateView
from otree.models import Session, Participant
from otree.views.export import get_export_response
# BLOCK FOR MTURK HITS
from otree.views.mturk import get_mturk_client
from otree_tools.models import EnterEvent, ExitEvent, FocusEvent
import json
from django.http import HttpResponse, StreamingHttpResponse
from .export import export_wide
from django.template import loader
import csv
from datetime import timedelta
from django.core.urlresolvers import reverse
from . import __version__ as otree_tools_version


# import otree_tools.forms as forms
# END OF BLOCK
# BLOCK FOR TESTING JSON THINGS
# from .forms import (UpdateExpirationForm)
# END OF BLOCK


# TIME STAMPS VIEWS FOR TRACKING_TIME and TRACKING_FOCUS
class EnterExitMixin:
    def get_queryset(self):
        # when we request num_exits>0 we get only those enter events which have some corresponding
        # exit events. we should sort them based on their exit type because form is submitted before or at the
        # same time as page is unloaded etc.
        earliest_exit = ExitEvent.objects.filter(enter_event=OuterRef('pk')).order_by('exit_type', 'timestamp')
        subquery_earliest = Subquery(earliest_exit.values('pk')[:1])

        tot_enter_events = EnterEvent.objects. \
            annotate(num_exits=Count('exits')). \
            filter(num_exits__gt=0). \
            annotate(
            early_exits=Min('exits__timestamp'),
            early_exit_pk=subquery_earliest,
            timediff=ExpressionWrapper(F('early_exits') - F('timestamp'),
                                       output_field=DurationField())
        )
        # TODO: later on think about efficiency of looping through all foo_display and replace exittype to

        for i in tot_enter_events:
            # for some weird reasons some random time diffs are not calculated at all (like None).
            if i.timediff is None:
                i.timediff = i.early_exits - i.timestamp

            i.exittype = ExitEvent.objects.get(pk=i.early_exit_pk).get_exit_type_display()

        return tot_enter_events


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
    template_name = 'otree_tools/all_timespent_list.html'
    url_name = 'time_spent_timestamps'
    url_pattern = r'^time_spent_per_page/$'
    display_name = 'Time spent per page [otree-tools]'
    context_object_name = 'timestamps'
    paginate_by = 50
    navbar_active_tag = 'time'
    export_link_name = 'enterexit_csv_export'


class FocusEventList(PaginatedListView):
    template_name = 'otree_tools/focus_event_list.html'
    url_name = 'focus_events'
    url_pattern = r'^focus_events/$'
    display_name = 'Focus/unfocus events [otree-tools]'
    context_object_name = 'focusevents'
    queryset = FocusEvent.objects.all()
    paginate_by = 50
    navbar_active_tag = 'focus'
    export_link_name = 'streaming_focus_csv'


class Echo:
    def write(self, value):
        return value


class StreamingCSVExport(ListView):
    response_class = StreamingHttpResponse
    content_type = 'text/csv'

    def iter_items(self, items, pseudo_buffer):
        writer = csv.DictWriter(pseudo_buffer, fieldnames=self.get_headers())
        yield writer.writerow(dict((fn, fn) for fn in self.get_headers()))

        for item in items:
            yield writer.writerow(self.get_data(item))

    def get(self, request, *args, **kwargs):
        response = StreamingHttpResponse(
            streaming_content=(self.iter_items(self.get_queryset(), Echo())),
            content_type='text/csv',
        )
        response['Content-Disposition'] = 'attachment;filename={}'.format(self.filename)
        return response


class StreamingFocusCSV(StreamingCSVExport):
    # todo: deal with coinciding time stamps of PageUnload and Form Submitted events
    url_name = 'streaming_focus_csv'
    url_pattern = r'^streaming_focusevent_csv_export/$'
    filename = 'focus_data.csv'

    def get_queryset(self):
        return FocusEvent.objects.all()

    def get_headers(self):
        return ['session_code', 'participant_code', 'app_name', 'round_number', 'page_name', 'timestamp',
                'event_desc_type', ]

    def get_data(self, item):
        #  unfortunately we can't make it more compact because reverse relations cannot be obtained with
        # general relations (or at least im too lazy to figure out how
        return {'session_code': item.participant.session.code,
                'participant_code': item.participant.code,
                'app_name': item.app_name,
                'round_number': item.player.round_number,
                'page_name': item.page_name,
                'timestamp': item.timestamp,
                'event_desc_type': item.event_desc_type}


class StreamingEnterCSV(EnterExitMixin, StreamingCSVExport):
    url_name = 'enterexit_csv_export'
    url_pattern = r'^enterexit_csv_export/$'
    filename = 'enter_exit_data.csv'

    def get_headers(self):
        return ['session_code', 'participant_code', 'app_name', 'round_number', 'page_name',
                'entrance_timestamp', 'exit_timestamp', 'duration', 'exit_type'
                ]

    def get_data(self, item):
        return {'session_code': item.participant.session.code,
                'participant_code': item.participant.code,
                'app_name': item.app_name,
                'round_number': item.player.round_number,
                'page_name': item.page_name,
                'entrance_timestamp': item.timestamp,
                'exit_timestamp': item.early_exits,
                'duration': item.timediff,
                'exit_type': item.exittype}


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


# End of welcoming page

# Dealin with individual session export - a list of all sessions goes first
class AllSessionsList(PaginatedListView):
    template_name = 'otree_tools/all_session_list.html'
    url_name = 'individual_sessions_export'
    url_pattern = r'^individual_sessions_export/$'
    display_name = 'Exporting data from individual sessions'
    navbar_active_tag = 'export'
    queryset = Session.objects.all()
    context_object_name = 'sessions'
    paginate_by = 10


# END OF BLOCK:: Dealin with individual session export - a list of all sessions goes first
# Block dealing with exporting participant vars #


class PVarsSessionsList(ListView):
    template_name = 'otree_tools/pvar_session_list.html'
    url_name = 'sessions_pvar_export'
    url_pattern = r'^sessions_pvar_export/$'
    display_name = 'Exporting Participant Vars [otree-tools]'
    model = Session
    context_object_name = 'sessions'


class UniversalEncoder(json.JSONEncoder):
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
    url_name = 'pvars_csv_export'
    url_pattern = r'^session/(?P<pk>[a-zA-Z0-9_-]+)/pvars_csv_export/$'
    response_class = HttpResponse
    content_type = 'text/csv'

    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type='text/csv')
        session_code = self.get_session().code
        filename = '{}_participant_vars.csv'.format(session_code)
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)

        pvars = self.get_queryset()
        writer = csv.writer(response)
        writer.writerow(self.heads)

        for p in pvars:
            writer.writerow(p)

        return response


# END OF Block dealing with exporting participant vars #


def check_if_deletable(h):
    if (h['HITStatus'] == 'Reviewable' and
                    h['NumberOfAssignmentsCompleted'] +
                    h['NumberOfAssignmentsAvailable'] == h['MaxAssignments']):
        h['Deletable'] = True
    return h


NO_CRED_ERR_CODE = 0
NO_CONN_ERR_CODE = 1


class MturkClient(object):
    client = None
    errors = None

    def get_errors(self):
        if self.errors == NO_CONN_ERR_CODE:
            return 'Sorry, there is no connection to Amazon mTurk web-site. Check your internet connection.'
        if self.errors == NO_CRED_ERR_CODE:
            return 'Sorry, I cannot find your Amazon credentials. Check your environment variables.'

    def __init__(self, use_sandbox=True):
        try:
            self.client = get_mturk_client(use_sandbox=use_sandbox)
            self.client.get_account_balance()
        except NoCredentialsError:
            self.client = None
            self.errors = NO_CRED_ERR_CODE
        except EndpointConnectionError:
            self.client = None
            self.errors = NO_CONN_ERR_CODE


class SpecificSessionDataView(vanilla.TemplateView):
    def get(self, request, *args, **kwargs):
        session_code = kwargs['session_code']
        response, file_extension = get_export_response(
            request, session_code)
        export_wide(response, file_extension, session_code=session_code)
        return response


class HitsList(vanilla.TemplateView):
    template_name = 'otree_tools/hits_list.html'
    url_name = 'hits_list'
    url_pattern = r'^hits_list/$'
    display_name = 'mTurk HITs'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        mturk = MturkClient()
        client = mturk.client

        if client is not None:
            balance = client.get_account_balance()['AvailableBalance']
            hits = client.list_hits()['HITs']
            for h in hits:
                h = check_if_deletable(h)
            context['balance'] = balance
            context['hits'] = hits
        else:
            context['mturk_errors'] = mturk.get_errors()

        return context


class AssignmentListView(vanilla.TemplateView):
    template_name = 'otree_tools/assignments_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_hit_id = self.kwargs.get('HITId')
        mturk = MturkClient()
        client = mturk.client
        if client is not None:
            cur_hit = check_if_deletable(client.get_hit(HITId=current_hit_id).get('HIT'))
            context['hit'] = cur_hit
            assignments = client.list_assignments_for_hit(HITId=current_hit_id)['Assignments']
            submitted_assignments = bool(
                {'Submitted', 'Rejected'} & set([a['AssignmentStatus'] for a in assignments]))
            context['assignments'] = assignments
            context['submitted_assignments'] = submitted_assignments
        else:
            context['mturk_errors'] = mturk.get_errors()
        return context

#
#
# class SendSomethingView(vanilla.FormView):
#     HITId = None
#     AssignmentId = None
#     WorkerId = None
#     Assignment = None
#
#     def dispatch(self, request, *args, **kwargs):
#         mturk = MturkClient()
#         client = mturk.client
#         if client is not None:
#             self.assignment = client.get_assignment(AssignmentId=kwargs['AssignmentID'])['Assignment']
#             self.AssignmentId = self.assignment['AssignmentId']
#             self.WorkerId = self.assignment['WorkerId']
#             self.HITId = self.assignment['HITId']
#         else:
#             self.context['mturk_errors'] = mturk.get_errors()
#         return super().dispatch(request, *args, **kwargs)
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['assignment'] = self.assignment
#         return context
#
#     def get_success_url(self):
#         return reverse('assignments_list', kwargs={'HITId': self.HITId})
#
#
# class SendMessageView(SendSomethingView):
#     form_class = forms.SendMessageForm
#     template_name = 'otree_tools/send_message.html'
#
#     def form_valid(self, form):
#         mturk = MturkClient()
#         client = mturk.client
#         if client is not None:
#             sending_message = client.notify_workers(
#                 Subject=form.cleaned_data['subject'],
#                 MessageText=form.cleaned_data['message_text'],
#                 WorkerIds=[self.WorkerId, ]
#             )
#         return super().form_valid(form)
#
#
# class SendBonusView(SendSomethingView):
#     template_name = 'otree_tools/send_bonus.html'
#     form_class = forms.SendBonusForm
#
#     def get_form(self, data=None, files=None, **kwargs):
#         max_bon = 100
#         mturk = MturkClient()
#         client = mturk.client
#         if client is not None:
#             response = client.list_bonus_payments(
#                 HITId=self.HITId,
#                 MaxResults=100,
#             )
#             bs = response['BonusPayments']
#             today = datetime.utcnow().date()
#             start = datetime(today.year, today.month, today.day, tzinfo=tz.tzutc())
#             recent_bs = [float(i['BonusAmount']) for i in bs if i['GrantTime'] > start]
#             tot_bon = sum([i for i in recent_bs])
#             max_bon = max(0, 100 - tot_bon)
#
#         cls = self.get_form_class()
#         return cls(data=data, files=files, max_bonus=max_bon)
#
#     def form_valid(self, form):
#         mturk = MturkClient()
#         client = mturk.client
#         if client is not None:
#             response = client.send_bonus(
#                 WorkerId=self.WorkerId,
#                 BonusAmount=str(form.cleaned_data['bonus_amount']),
#                 AssignmentId=self.AssignmentId,
#                 Reason=form.cleaned_data['reason'],
#             )
#         return super().form_valid(form)
#
#
# class DeleteHitView(vanilla.View):
#     def get(self, request, *args, **kwargs):
#         mturk = MturkClient()
#         client = mturk.client
#         if client is not None:
#             cur_hit = check_if_deletable(client.get_hit(HITId=self.kwargs['HITId']).get('HIT'))
#             if cur_hit.get('Deletable'):
#                 response = client.delete_hit(HITId=cur_hit['HITId'])
#
#         return HttpResponseRedirect(reverse_lazy('hits_list'))
#
#
# class UpdateExpirationView(vanilla.FormView):
#     back_to_HIT = None
#     form_class = UpdateExpirationForm
#     template_name = 'otree_tools/update_expiration.html'
#     HITId = None
#     HIT = None
#
#     def get_form(self, data=None, files=None, **kwargs):
#         cls = self.get_form_class()
#         return cls(data=data, files=files, initial={'expire_time': self.HIT['Expiration']})
#
#     def get_success_url(self):
#         if self.back_to_HIT:
#             return reverse('assignments_list', kwargs={'HITId': self.HITId})
#         else:
#             return reverse_lazy('hits_list')
#
#     def dispatch(self, request, *args, **kwargs):
#
#         mturk = MturkClient()
#         client = mturk.client
#         if client is not None:
#             self.HITId = kwargs['HITId']
#             self.HIT = client.get_hit(HITId=self.HITId).get('HIT')
#         else:
#             self.context['mturk_errors'] = mturk.get_errors()
#         return super().dispatch(request, *args, **kwargs)
#
#     def form_valid(self, form):
#         mturk = MturkClient()
#         client = mturk.client
#         if client is not None:
#             response = client.update_expiration_for_hit(
#                 HITId=self.HITId,
#                 ExpireAt=0  # form.cleaned_data['expire_time']
#             )
#             response = client.update_expiration_for_hit(
#                 HITId=self.HITId,
#                 ExpireAt=form.cleaned_data['expire_time']
#             )
#         return super().form_valid(form)
#
#
# class ExpireHitView(vanilla.View):
#     back_to_HIT = None
#
#     def get(self, request, *args, **kwargs):
#         mturk = MturkClient()
#         client = mturk.client
#         if client is not None:
#             response = client.update_expiration_for_hit(
#                 HITId=self.kwargs['HITId'],
#                 ExpireAt=0,
#             )
#         if self.back_to_HIT:
#             return HttpResponseRedirect(reverse('assignments_list', kwargs={'HITId': self.kwargs['HITId']}))
#         else:
#             return HttpResponseRedirect(reverse_lazy('hits_list'))
#
#
# class ApproveAssignmentView(vanilla.FormView):
#     form_class = forms.ApproveAssignmentForm
#     template_name = 'otree_tools/approve_assignment.html'
#     success_url = reverse_lazy('hits_list')
#
#     def get(self, request, *args, **kwargs):
#         return super().get(request, *args, **kwargs)
#
#     def form_valid(self, form):
#         mturk = MturkClient()
#         client = mturk.client
#         if client is not None:
#             response = client.approve_assignment(
#                 AssignmentId=self.kwargs['AssignmentID'],
#                 RequesterFeedback=form.cleaned_data['message_text'],
#                 OverrideRejection=True,
#             )
#         return super().form_valid(form)
#
#
# class RejectAssignmentView(vanilla.FormView):
#     form_class = forms.RejectAssignmentForm
#     template_name = 'otree_tools/reject_assignment.html'
#     success_url = reverse_lazy('hits_list')
#
#     def form_valid(self, form):
#         mturk = MturkClient()
#         client = mturk.client
#         if client is not None:
#             response = client.reject_assignment(
#                 AssignmentId=self.kwargs['AssignmentID'],
#                 RequesterFeedback=form.cleaned_data['message_text'],
#             )
#         return super().form_valid(form)
