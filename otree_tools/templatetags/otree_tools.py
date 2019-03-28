from datetime import timedelta
from django import template
from django.template import TemplateSyntaxError, Context
from otree_tools.models.models import FOCUS_EVENT_TYPES, EXITTYPES

d_focus_event_types = dict(FOCUS_EVENT_TYPES)


class ButtonTagError(Exception):
    pass


register = template.Library()
# two following random strings are needed to prevent usage of tracking_time and tracking_focus twice
# see more here: https://stackoverflow.com/questions/51786795/check-that-tag-is-used-in-template-only-once/
tracking_time_code, tracking_focus_code = 'xBl4fTBP8hAsg61o1gJa', 'Q4YviMPgcVUjbbm05C6s'


def universal_tracker(context, tagname):
    context['page_index'] = context['view']._index_in_pages
    context['page_name'] = context['view'].__class__.__name__
    code = globals()[f'{tagname}_code']
    if code in context:
        formatted_tag_name = '{{% {} %}}'.format(tagname)
        raise Exception(f'{formatted_tag_name} is already used')
    context[code] = True
    return context


@register.inclusion_tag('otree_tools/tags/TimeTracker.html', takes_context=True)
def tracking_time(context, wait_for_images=True, *args, **kwargs):
    context['wait_for_images'] = wait_for_images
    return universal_tracker(context, 'tracking_time')


@register.inclusion_tag('otree_tools/tags/FocusTracker.html', takes_context=True, name='tracking_focus')
def tracking_focus_func(context, *args, **kwargs):
    c = universal_tracker(context, 'tracking_focus')
    c['type_correspondence'] = d_focus_event_types
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


@register.filter
def convert_exit(value):
    return dict(EXITTYPES)[int(value)]


@register.filter
def duration(value):
    return timedelta(milliseconds=int(value)/1000)
