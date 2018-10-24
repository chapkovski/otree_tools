from django.forms import widgets
import numbers
import math
from otree.widgets import CheckboxSelectMultiple

# for decompression
divider = ':'


class NoCheckboxCheckbox(CheckboxSelectMultiple):
    input_type = 'radiobutton'
    template_name = 'otree_tools/widgets/multiple_choice_select.html'
    option_template_name = 'otree_tools/widgets/multiple_choice_option.html'

    class Media:
        css = {'all': ('css/otree_tools_widgets.css',)}

    def build_attrs(self, base_attrs, extra_attrs=None):
        b = super().build_attrs(base_attrs, extra_attrs)
        b['class'] = 'form-check-input otree-tools-checkbox'
        return b


class OtherTextInput(widgets.TextInput):
    is_required = False

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        if context['widget']['attrs'].get('required'):
            context['widget']['attrs'].pop('required')
        context['other_text_input'] = name
        return context


class OtherSelectorWidget(widgets.MultiWidget):
    template_name = 'otree_tools/widgets/multiwidget.html'

    def __init__(self, other_val='other', choices=None, attrs=None):
        self.choices = choices
        self.other_val = other_val;
        _widgets = (
            widgets.RadioSelect(choices=choices, attrs={'class': 'other_wg_radio_group'}),
            OtherTextInput(attrs={'class': 'hidden_text_group', }, ),
        )
        super().__init__(_widgets, attrs)

    def get_context(self, name, value, attrs):
        con = super().get_context(name, value, attrs)
        con['wrap_label'] = True
        con['other_val'] = self.other_val
        # this one is needed only for a yet empty field
        if isinstance(value, list):
            con['widget']['show_other_inbox'] = value[0] == self.other_val
        else:
            if isinstance(value, str):
                con['widget']['show_other_inbox'] = self.decompress(value)[0] == self.other_val
        return con

    def decompress(self, value):
        # TODO what if someone starts his other answer with trailing divider? ignore for now

        if value:
            split_value = value.split(divider)
            if len(split_value) > 1:
                is_other = split_value[0] == self.other_val
                the_rest = ''.join(split_value[1:])
            else:
                is_other = False
                the_rest = ''
            if is_other:
                return [self.other_val, the_rest]
            else:
                return [value, '']
        return [None, None, ]

    def format_output(self, rendered_widgets):
        return ''.join(rendered_widgets)

    def value_from_datadict(self, data, files, name):
        radio_data = self.widgets[0].value_from_datadict(data, files, name + '_0')
        text_data = self.widgets[1].value_from_datadict(data, files, name + '_1')
        return [radio_data, text_data]


permitted_info_block = ['left', 'right']
non_permitted_block_msg = 'Choose between two options: {}'.format(' or '.join(permitted_info_block))
no_range_set_err_msg = 'Both max and min parameters should be set to use this slider'


class AdvancedSliderWidget(widgets.NumberInput):
    template_name = 'otree_tools/widgets/tickslider.html'
    # TODO: provide a chance for user not to give min and max
    # default_min = 0
    # default_max = 10
    # default_range = 10
    default_nsteps = 10
    default_med_value = 5
    ndigits = 0
    suffix = ''

    def __init__(self, show_ticks=True, show_value=True, show_block='left', ndigits=None, *args, **kwargs):
        self.show_ticks = show_ticks
        self.show_value = show_value
        self.ndigits = ndigits
        assert show_block in permitted_info_block, non_permitted_block_msg
        self.show_block = show_block
        super().__init__(*args, **kwargs)

    def set_steps(self, smin, smax):
        slider_range = smax - smin
        step = round(slider_range / self.default_nsteps, 2)
        return step

    def set_digits(self, step):
        if self.ndigits is None:
            if isinstance(step, int):
                self.ndigits = 0
                return
            frac, _ = math.modf(step)
            strfrac = str(frac).split('.')[1]
            self.ndigits = len(strfrac)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        a_ = context['widget']['attrs']
        assert all(i in a_ for i in ['min', 'max']), no_range_set_err_msg
        # TODO: allow user to skip max/min providing default options (partly based on step/tick_interval options)
        # wi_attrs.setdefault('min', self.default_min)
        # wi_attrs.setdefault('max', self.default_max)
        if not isinstance(a_.get('step'), numbers.Number):
            a_['step'] = self.set_steps(a_['min'], a_['max'])
        self.set_digits(a_['step'])
        a_['ndigits'] = self.ndigits

        a_.setdefault('tick_interval', a_['step'])
        a_.setdefault('secondary_ticks', True)
        a_.setdefault('show_ticks', True)
        self.default_med_value = round((a_['min'] + a_['max']) / 2, self.ndigits)
        if self.ndigits == 0:
            self.default_med_value = int(self.default_med_value)
        a_['slider_start_value'] = value if value is not None else self.default_med_value
        a_.setdefault('suffix', self.suffix)
        a_['show_value'] = self.show_value
        a_['show_block'] = self.show_block
        return context



        # TODO: when Chris includes form.media to the template, stop adding jquery-ui to each field which is absu
        # class Media:
        #     css = {
        #         'all': ('jquery-ui/jquery-ui.min.css',
        #                 'css/slider.css',)
        #     }
        #     js = ('jquery-ui/jquery-ui.min.js',
        #           'js/slider.js',)
