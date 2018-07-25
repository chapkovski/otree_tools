from otree.views.export import get_export_response
import vanilla
from .export import export_wide
from otree.models import Session
from django.shortcuts import render

# BLOCK FOR MTURK HITS
from django.conf import settings
from otree.views.mturk import get_mturk_client
from botocore.exceptions import NoCredentialsError, EndpointConnectionError
import json
from django.core.urlresolvers import reverse, reverse_lazy
import otree_tools.forms as forms
from django.http import JsonResponse, HttpResponseRedirect
from datetime import datetime, timedelta, timezone
from dateutil import tz
# END OF BLOCK

# BLOCK FOR TESTING JSON THINGS

from django.http import JsonResponse
from django.template.loader import render_to_string
from .forms import (UpdateExpirationForm)

# END OF BLOCK

from contextlib import contextmanager


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


class AllSessionsList(vanilla.TemplateView):
    template_name = 'otree_tools/all_session_list.html'
    url_name = 'individual_sessions_export'
    url_pattern = r'^individual_sessions_export/$'
    display_name = 'Exporting data from individual sessions'

    def get(self, request, *args, **kwargs):
        all_sessions = Session.objects.all()
        return render(request, self.template_name, {'sessions': all_sessions})


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


class SendSomethingView(vanilla.FormView):
    HITId = None
    AssignmentId = None
    WorkerId = None
    Assignment = None

    def dispatch(self, request, *args, **kwargs):
        mturk = MturkClient()
        client = mturk.client
        if client is not None:
            self.assignment = client.get_assignment(AssignmentId=kwargs['AssignmentID'])['Assignment']
            self.AssignmentId = self.assignment['AssignmentId']
            self.WorkerId = self.assignment['WorkerId']
            self.HITId = self.assignment['HITId']
        else:
            self.context['mturk_errors'] = mturk.get_errors()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['assignment'] = self.assignment
        return context

    def get_success_url(self):
        return reverse('assignments_list', kwargs={'HITId': self.HITId})


class SendMessageView(SendSomethingView):
    form_class = forms.SendMessageForm
    template_name = 'otree_tools/send_message.html'

    def form_valid(self, form):
        mturk = MturkClient()
        client = mturk.client
        if client is not None:
            sending_message = client.notify_workers(
                Subject=form.cleaned_data['subject'],
                MessageText=form.cleaned_data['message_text'],
                WorkerIds=[self.WorkerId, ]
            )
        return super().form_valid(form)


class SendBonusView(SendSomethingView):
    template_name = 'otree_tools/send_bonus.html'
    form_class = forms.SendBonusForm

    def get_form(self, data=None, files=None, **kwargs):
        max_bon = 100
        mturk = MturkClient()
        client = mturk.client
        if client is not None:
            response = client.list_bonus_payments(
                HITId=self.HITId,
                MaxResults=100,
            )
            bs = response['BonusPayments']
            today = datetime.utcnow().date()
            start = datetime(today.year, today.month, today.day, tzinfo=tz.tzutc())
            recent_bs = [float(i['BonusAmount']) for i in bs if i['GrantTime'] > start]
            tot_bon = sum([i for i in recent_bs])
            max_bon = max(0, 100 - tot_bon)

        cls = self.get_form_class()
        return cls(data=data, files=files, max_bonus=max_bon)

    def form_valid(self, form):
        mturk = MturkClient()
        client = mturk.client
        if client is not None:
            response = client.send_bonus(
                WorkerId=self.WorkerId,
                BonusAmount=str(form.cleaned_data['bonus_amount']),
                AssignmentId=self.AssignmentId,
                Reason=form.cleaned_data['reason'],
            )
        return super().form_valid(form)


class DeleteHitView(vanilla.View):
    def get(self, request, *args, **kwargs):
        mturk = MturkClient()
        client = mturk.client
        if client is not None:
            cur_hit = check_if_deletable(client.get_hit(HITId=self.kwargs['HITId']).get('HIT'))
            if cur_hit.get('Deletable'):
                response = client.delete_hit(HITId=cur_hit['HITId'])

        return HttpResponseRedirect(reverse_lazy('hits_list'))


class UpdateExpirationView(vanilla.FormView):
    back_to_HIT = None
    form_class = UpdateExpirationForm
    template_name = 'otree_tools/update_expiration.html'
    HITId = None
    HIT = None

    def get_form(self, data=None, files=None, **kwargs):
        cls = self.get_form_class()
        # print()
        return cls(data=data, files=files, initial={'expire_time': self.HIT['Expiration']})

    def get_success_url(self):
        if self.back_to_HIT:
            return reverse('assignments_list', kwargs={'HITId': self.HITId})
        else:
            return reverse_lazy('hits_list')

    def dispatch(self, request, *args, **kwargs):

        mturk = MturkClient()
        client = mturk.client
        if client is not None:
            self.HITId = kwargs['HITId']
            self.HIT = client.get_hit(HITId=self.HITId).get('HIT')
        else:
            self.context['mturk_errors'] = mturk.get_errors()
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        mturk = MturkClient()
        client = mturk.client
        if client is not None:
            response = client.update_expiration_for_hit(
                HITId=self.HITId,
                ExpireAt=0  # form.cleaned_data['expire_time']
            )
            response = client.update_expiration_for_hit(
                HITId=self.HITId,
                ExpireAt=form.cleaned_data['expire_time']
            )
        return super().form_valid(form)


class ExpireHitView(vanilla.View):
    back_to_HIT = None

    def get(self, request, *args, **kwargs):
        mturk = MturkClient()
        client = mturk.client
        if client is not None:
            response = client.update_expiration_for_hit(
                HITId=self.kwargs['HITId'],
                ExpireAt=0,
            )
        if self.back_to_HIT:
            return HttpResponseRedirect(reverse('assignments_list', kwargs={'HITId': self.kwargs['HITId']}))
        else:
            return HttpResponseRedirect(reverse_lazy('hits_list'))


class ApproveAssignmentView(vanilla.FormView):
    form_class = forms.ApproveAssignmentForm
    template_name = 'otree_tools/approve_assignment.html'
    success_url = reverse_lazy('hits_list')

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        mturk = MturkClient()
        client = mturk.client
        if client is not None:
            response = client.approve_assignment(
                AssignmentId=self.kwargs['AssignmentID'],
                RequesterFeedback=form.cleaned_data['message_text'],
                OverrideRejection=True,
            )
        return super().form_valid(form)


class RejectAssignmentView(vanilla.FormView):
    form_class = forms.RejectAssignmentForm
    template_name = 'otree_tools/reject_assignment.html'
    success_url = reverse_lazy('hits_list')

    def form_valid(self, form):
        mturk = MturkClient()
        client = mturk.client
        if client is not None:
            response = client.reject_assignment(
                AssignmentId=self.kwargs['AssignmentID'],
                RequesterFeedback=form.cleaned_data['message_text'],
            )
        return super().form_valid(form)
