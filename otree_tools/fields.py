from django.db import models
import json
from .widgets import OtherSelectorWidget, divider
from django.forms.fields import MultiValueField, CharField, MultipleChoiceField, ChoiceField
from otree.common_internal import expand_choice_tuples
from django.core.exceptions import ValidationError
from django.forms import CheckboxSelectMultiple

from django.core import checks

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


class MultiSelectFormField(MultipleChoiceField):
    widget = CheckboxSelectMultiple

    def __init__(self, *args, **kwargs):
        self.max_choices = kwargs.pop('max_choices', 0)
        super(MultiSelectFormField, self).__init__(*args, **kwargs)

    def clean(self, value):
        if not value and self.required:
            raise ValidationError(self.error_messages['required'])
        # todo: pluralize max_choices
        if value and self.max_choices and len(value) > self.max_choices:
            raise ValidationError('You must select a maximum of {} choices.'.format(self.max_choices))
        return value


class ListField(models.CharField):
    def check(self, **kwargs):
        errors = super().check(**kwargs)
        if self.inner_choices is None:
            errors.extend([
                checks.Error(
                    "ListField should be provided with choices",
                    obj=self,
                    id='fields.E919',
                )
            ])
        if not isinstance(self.inner_choices, (list, tuple)):
            errors.extend([
                checks.Error(
                    "ListField should be provided with choices parameter: either list or tuple",
                    obj=self,
                    id='fields.E920',
                )
            ])
        # TODO: what if default is not in choices?
        # TODO: add label/verbose name, and other stuff
        default_value = self.initial

        if default_value is not None:
            if not isinstance(default_value, (list, tuple)):
                errors.extend([
                    checks.Error(
                        "Initial value should be either list or tuple",
                        obj=self,
                        id='fields.E921',
                    )
                ])
            inner_choices_flat = [i[0] for i in self.inner_choices]
            if not all(i in inner_choices_flat for i in default_value):
                errors.extend([
                    checks.Error(
                        "Initial values should be item(s) in your 'choices' list",
                        obj=self,
                        id='fields.E921',
                    )
                ])
        return errors

    def __init__(
            self,
            *,
            choices=None,
            max_choices=None,
            label=None,
            max_length=10000,
            doc='',
            initial=None,
            blank=False,
            **kwargs):

        kwargs.update(dict(
            choices=choices,
            label=label,
            initial=initial,
            max_choices=max_choices,
        ))

        self.inner_choices = kwargs.pop('choices', None)
        if self.inner_choices is not None:
            self.max_choices = kwargs.pop('max_choices', len(self.inner_choices))
        else:
            kwargs.pop('max_choices')
        self.initial = initial
        kwargs.setdefault('help_text', '')
        kwargs.setdefault('null', True)
        label = kwargs['label']
        kwargs.setdefault('verbose_name', label)
        kwargs.setdefault('default', kwargs.pop('initial', None))
        self.initial = kwargs['default']
        if isinstance(self.inner_choices, (list, tuple)):
            self.inner_choices = list(expand_choice_tuples(self.inner_choices))
        kwargs.setdefault('verbose_name', kwargs.pop('label'))
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
            return MultiSelectFormField(choices=self.inner_choices,
                                        label=self.verbose_name, required=not self.blank,
                                        widget=CheckboxSelectMultiple(choices=self.inner_choices),
                                        max_choices=self.max_choices,
                                        **kwargs)
