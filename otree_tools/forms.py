import floppyforms as forms




class SendBonusForm(forms.Form):
    def __init__(self, max_bonus, *args,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields['bonus_amount']=forms.FloatField(min_value=0, max_value=max_bonus)
        self.fields['reason'] = forms.CharField(widget=forms.Textarea)


class SendMessageForm(forms.Form):
    subject = forms.CharField(max_length=100)
    message_text = forms.CharField(widget=forms.Textarea)


class ApproveAssignmentForm(forms.Form):
    message_text = forms.CharField(widget=forms.Textarea, required=False)


class RejectAssignmentForm(forms.Form):
    message_text = forms.CharField(widget=forms.Textarea, required=False)


from datetimewidget.widgets import DateTimeWidget, DateWidget, TimeWidget

class UpdateExpirationForm(forms.Form):
    expire_time = forms.DateTimeField(widget=DateTimeWidget(usel10n=True, bootstrap_version=3))
