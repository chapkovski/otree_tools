from django.db import models
import json
from .widgets import OtherSelectorWidget, divider
from django.forms.fields import MultiValueField, CharField
from otree.common_internal import expand_choice_tuples
from django.core.exceptions import ValidationError

duplicate_err_msg = 'One of the choices duplicates with the internal name for "Other" choice field'
wrong_value_msg = 'Please provide a valid name for other_value. It should look like Python variable (no spaces etc.)'


class OtherModelField(models.CharField):
    other_value = None
    other_label = None

    def __init__(self, max_length=10000,
                 blank=False,
                 label=None,
                 *args, **kwargs):
        kwargs.update(dict(label=label, ))
        kwargs.setdefault('help_text', '')
        kwargs.setdefault('null', True)
        kwargs.setdefault('verbose_name', kwargs.pop('label'))
        self.other_value = kwargs.pop('other_value', None)
        self.other_label = kwargs.pop('other_label', None)
        self.inner_choices = kwargs.pop('choices', None)
        super().__init__(max_length=max_length, blank=blank, *args, **kwargs)

    def formfield(self, **kwargs):
        return OtherFormField(other_value=self.other_value, other_label=self.other_label, choices=self.inner_choices,
                              label=self.verbose_name, required=not self.blank,
                              **kwargs)


class OtherFormField(MultiValueField):
    other_value = 'other_'
    other_label = 'Other'
    required = True

    def __init__(self, other_value=None, other_label=None, label='', **kwargs):

        self.choices = kwargs.pop('choices')
        if other_label:
            self.other_label = other_label
        if other_value:
            self.other_value = other_value
        # check that other_value provided is valid
        assert self.other_value.isidentifier(), wrong_value_msg
        self.choices = list(expand_choice_tuples(self.choices))
        flat_choices = [i for i, j in self.choices]
        # check if value of choices start with other_val and divider, like 'other: SOMETHING'
        for i in flat_choices:
            assert not i.startswith(self.other_value), duplicate_err_msg
        self.choices += [(self.other_value, self.other_label), ]
        self.widget = OtherSelectorWidget(choices=self.choices, other_val=self.other_value)
        fields = (CharField(required=self.required), CharField(required=False),)
        super().__init__(fields=fields, require_all_fields=False, label=label, **kwargs)

    def compress(self, data_list):
        # this fallback is needed only if the field is blank
        if len(data_list) > 0:
            if data_list[0] == self.other_value:
                if data_list[1] in (None, ''):
                    raise ValidationError(u'Please provide the answer for "{}" field'.format(self.other_label))
                return '{}{}{}'.format(self.other_value, divider, data_list[1])
            else:
                return data_list[0]
