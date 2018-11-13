from django import template
from django.template import TemplateSyntaxError, Context
from otree_tools.models.models import FOCUS_EVENT_TYPES


class ButtonTagError(Exception):
    pass


register = template.Library()
# two following random strings are needed to prevent usage of tracking_time and tracking_focus twice
# see more here: https://stackoverflow.com/questions/51786795/check-that-tag-is-used-in-template-only-once/
tracking_time_code, tracking_focus_code = 'xBl4fTBP8hAsg61o1gJa', 'Q4YviMPgcVUjbbm05C6s'


def universal_tracker(context, tagname):
    context['page_index'] = context['view']._index_in_pages
    context['page_name'] = context['view'].__class__.__name__
    code = globals()['{}_code'.format(tagname)]
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
    c = universal_tracker(context, 'tracking_focus')
    c['type_correspondence'] = {i: j for i, j in FOCUS_EVENT_TYPES}
    return c


@register.inclusion_tag('otree_tools/tags/Button.html', takes_context=True)
def button(context, label='', *args, **kwargs):
    for kwarg in kwargs:
        raise ButtonTagError(
            # need double {{ to escape because of .format()
            '{{% button %}} tag received unrecognized parameter "{}"'.format(kwarg)
        )
    context['label'] = label
    return context


@register.inclusion_tag('otree_tools/tags/ConfirmButton.html', takes_context=True, name='confirm_button')
def confirm_button(context,
                   title='Info',
                   message='Are you sure you would like to proceed?',
                   main_button='Next',
                   yes_button='Yes',
                   no_button='No'):
    c = context
    c['title'] = title
    c['message'] = message
    c['main_button'] = main_button
    c['yes_button'] = yes_button
    c['no_button'] = no_button
    return c
