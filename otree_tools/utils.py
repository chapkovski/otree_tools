from otree.models_concrete import PageCompletion


def get_seconds_per_page(player, page_name):
    participant = player.participant
    subsession_pk = player.subsession.pk
    try:
        page_info = PageCompletion.objects.get(participant=participant, subsession_pk=subsession_pk,
                                               page_name=page_name)
    except PageCompletion.DoesNotExist:
        raise ValueError('Cannot find info about this page')
    return page_info.seconds_on_page
