from otree_tools.widgets import OtherSelectorWidget, divider
from django.forms.fields import MultiValueField, CharField, MultipleChoiceField, ChoiceField
from otree.common_internal import expand_choice_tuples
from django.core.exceptions import ValidationError
from django.forms import CheckboxSelectMultiple

duplicate_err_msg = 'One of the choices duplicates with the internal name for "Other" choice field'
wrong_value_msg = 'Please provide a valid name for other_value. It should look like Python variable (no spaces etc.)'
wrong_type_err_msg = 'Please provide a choices option for ListField which should be either a list or tuple of values'


class OtherFormField(MultiValueField):
    other_value = 'other_'
    other_label = 'Other'
    required = True

    # def __setattr__(self, name, value):
    #     super().__setattr__(name, value)
    #     if name == 'choices':
    #         print('CHANGING TO:::', value)
    #         self.widget.choices=value
    #         print('QQQQQ',self.widget.__dict__)

    def __init__(self, other_value=None, other_label=None, label='', **kwargs):

        self.choices = kwargs.pop('choices')
        if other_label:
            self.other_label = other_label
        if other_value:
            self.other_value = other_value
        # check that other_value provided is valid
        assert self.other_value.isidentifier(), wrong_value_msg
        if isinstance(self.choices, (list, tuple)) and len(self.choices) > 0:
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
