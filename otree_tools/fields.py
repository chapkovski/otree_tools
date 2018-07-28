from django.db import models
import json
from .widgets import OtherSelectorWidget, divider
from django.forms.fields import MultiValueField, CharField, MultipleChoiceField
from otree.common_internal import expand_choice_tuples
from django.core.exceptions import ValidationError
from django.forms import CheckboxSelectMultiple
from django.core import  checks
duplicate_err_msg = 'One of the choices duplicates with the internal name for "Other" choice field'
wrong_value_msg = 'Please provide a valid name for other_value. It should look like Python variable (no spaces etc.)'
wrong_type_err_msg = 'Please provide a choices option for ListField which should be either a list or tuple of values'


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


class ListField(models.CharField):
    def check(self, **kwargs):

        errors = super().check(**kwargs)
        if self.inner_choices is None:
            errors.extend([
                checks.Error(
                    "'ListField should be provided with choices'",
                    obj=self,
                    id='fields.E919',
                )
                ])
        return errors

    def __init__(
            self,
            *,
            choices=None,
            max_length=10000,
            blank=False,
            **kwargs):
        kwargs.update(dict(
            choices=choices,
        ))
        self.inner_choices=kwargs.pop('choices', None)
        kwargs.setdefault('help_text', '')
        kwargs.setdefault('null', True)
        if isinstance(self.inner_choices, (list, tuple)):
            self.inner_choices = list(expand_choice_tuples(self.inner_choices))

        super().__init__(
            choices=None,
            max_length=max_length,
            blank=None,
            **kwargs)

    def from_db_value(self, value, expression, connection, context):
        return self.to_python(value)

    def to_python(self, value):
        if isinstance(value, list):
            return value

        if value is None:
            return value

        return json.loads(value)

    def get_prep_value(self, value):
        return json.dumps(value)

    def formfield(self, **kwargs):
        if self.inner_choices is not None:
            return MultipleChoiceField(choices=self.inner_choices,
                                       label=self.verbose_name, required=not self.blank,
                                       widget=CheckboxSelectMultiple(choices=self.inner_choices),
                                       **kwargs)

# widget=forms.CheckboxSelectMultiple(choices=OPTIONS),
