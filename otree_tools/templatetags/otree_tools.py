from django import template


class ButtonTagError(Exception):
    pass


register = template.Library()


@register.inclusion_tag('otree_tools/tags/TimeTracker.html', takes_context=True)
def tracking_time(context, *args, **kwargs):
    participant = context['participant']
    return context


@register.inclusion_tag('otree_tools/tags/Button.html', takes_context=True)
def button(context, label='', *args, **kwargs):
    for kwarg in kwargs:
        raise ButtonTagError(
            # need double {{ to escape because of .format()
            '{{% chat %}} tag received unrecognized parameter "{}"'.format(kwarg)
        )
    context['label'] = label
    return context
