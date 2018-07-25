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
    template_name = 'widgets/multiwidget.html'

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
