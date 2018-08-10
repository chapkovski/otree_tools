from django import template
from django.template import TemplateSyntaxError, Context


class ButtonTagError(Exception):
    pass


register = template.Library()
# two following random strings are needed to prevent usage of tracking_time and tracking_focus twice
# see more here: https://stackoverflow.com/questions/51786795/check-that-tag-is-used-in-template-only-once/
tracking_time_code, tracking_focus_code ='xBl4fTBP8hAsg61o1gJa','Q4YviMPgcVUjbbm05C6s'


def universal_tracker(context, tagname):
    context['page_name'] = context['view'].__class__.__name__
    code =globals()['{}_code'.format(tagname)]
    if code in context:
        formatted_tag_name = '{{% {} %}}'.format(tagname)
        raise Exception('{} is already used'.format(formatted_tag_name))
    context[code] = True
    return context

@register.inclusion_tag('otree_tools/tags/TimeTracker.html', takes_context=True)
def tracking_time(context, *args, **kwargs):
    return universal_tracker(context, 'tracking_time')


@register.inclusion_tag('otree_tools/tags/FocusTracker.html', takes_context=True, name='tracking_focus')
def tracking_focus_func(context, *args, **kwargs):
    return universal_tracker(context, 'tracking_focus')


@register.inclusion_tag('otree_tools/tags/Button.html', takes_context=True)
def button(context, label='', *args, **kwargs):
    for kwarg in kwargs:
        raise ButtonTagError(
            # need double {{ to escape because of .format()
            '{{% chat %}} tag received unrecognized parameter "{}"'.format(kwarg)
        )
    context['label'] = label
    return context



