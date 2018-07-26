from django.forms import widgets

# for decompression
divider = ':'


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
        # print('VALUE::::', self.decompress(value))
        if isinstance(value, list):
            con['widget']['show_other_inbox'] =  value[0] == self.other_val
        else:
            if isinstance(value, str):
                con['widget']['show_other_inbox'] = self.decompress(value)[0]== self.other_val
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


class AdvancedSliderWidget(widgets.NumberInput):
    template_name = 'otree_tools/widgets/tickslider.html'
    default_min = 0
    default_max = 10
    defaul_med_value = 5
    default_step = 1

    def __init__(self, show_ticks=True, show_value=True, show_block='left', *args, **kwargs):
        self.show_ticks = show_ticks
        self.show_value = show_value
        assert show_block in permitted_info_block, non_permitted_block_msg
        self.show_block = show_block
        super().__init__(*args, **kwargs)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        wi_attrs = context['widget']['attrs']
        wi_attrs.setdefault('min', self.default_min)
        wi_attrs.setdefault('max', self.default_max)
        wi_attrs.setdefault('step', self.default_step)
        wi_attrs.setdefault('tick_interval', self.default_step)
        wi_attrs.setdefault('secondary_ticks', True)
        wi_attrs.setdefault('show_ticks', True)
        self.defaul_med_value = (wi_attrs['min'] + wi_attrs['max']) / 2
        wi_attrs['slider_start_value'] = int(value) if value is not None else int(self.defaul_med_value)
        wi_attrs['show_value'] = self.show_value
        wi_attrs['show_block'] = self.show_block

        return context



        # TODO: when Chris includes form.media to the template, stop adding jquery-ui to each field which is absu
        # class Media:
        #     css = {
        #         'all': ('jquery-ui/jquery-ui.min.css',
        #                 'css/slider.css',)
        #     }
        #     js = ('jquery-ui/jquery-ui.min.js',
        #           'js/slider.js',)
