from django.db import models
import json
from django.core import checks
from otree_tools.forms.fields import OtherFormField, MultiSelectFormField
from otree.widgets import CheckboxSelectMultiple
from otree.common_internal import expand_choice_tuples
from otree_tools.radiogrid import RadioGridField
from otree_tools.widgets import NoCheckboxCheckbox


class InnerChoiceMixin:
    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        if name == 'choices':
            if isinstance(value, (list, tuple)) and len(value) > 0:
                self.inner_choices = list(expand_choice_tuples(value))


class OtherModelField(InnerChoiceMixin, models.CharField):
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


class ListField(models.CharField):
    def __init__(
            self,
            *,
            max_length=10000,
            blank=False,
            **kwargs):

        kwargs.setdefault('help_text', '')
        kwargs.setdefault('null', True)

        super().__init__(
            max_length=max_length,
            blank=blank,
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


class MultipleChoiceModelField(InnerChoiceMixin, ListField):
    default_length = 3

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
                        id='fields.E922',
                    )
                ])
        return errors

    def __init__(
            self,
            *,
            choices=None,
            max_choices=None,
            min_choices=None,
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
            min_choices=min_choices,
        ))

        self.inner_choices = kwargs.pop('choices', None)
        if self.inner_choices is not None:
            self.max_choices = kwargs.pop('max_choices', len(self.inner_choices))
            self.min_choices = kwargs.pop('min_choices', 0)
        else:
            self.max_choices = kwargs.pop('max_choices', None)
            self.min_choices = kwargs.pop('min_choices', None)
            if self.max_choices:
                self.inner_choices = [str(i) for i in range(1, self.max_choices + 1)]
            else:
                if self.min_choices:
                    self.inner_choices = [str(i) for i in range(1, self.min_choices + 1)]
                else:
                    self.inner_choices = [str(i) for i in range(1, self.default_length)]

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

    def formfield(self, **kwargs):
        if self.inner_choices is not None:
            return MultiSelectFormField(choices=self.inner_choices,
                                        label=self.verbose_name, required=not self.blank,
                                        widget=NoCheckboxCheckbox(choices=self.inner_choices),
                                        max_choices=self.max_choices,
                                        min_choices=self.min_choices,
                                        **kwargs)
