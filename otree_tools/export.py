

from otree.models import Participant, Session
from otree.export import get_field_names_for_csv, sanitize_for_csv, get_rows_for_wide_csv_round, get_models_module, \
    get_payoff_plus_participation_fee, _export_xlsx,_export_csv
from otree.session import SessionConfig
import collections
from collections import OrderedDict
from django.conf import settings
from django.db.models import Max



def get_rows_for_wide_csv(session_code):
    cursession=Session.objects.get(code=session_code)
    sessions = [cursession]
    session_cache = {row.id: row for row in sessions}
    session_config_fields = set()
    for session in sessions:
        for field_name in SessionConfig(session.config).editable_fields():
            session_config_fields.add(field_name)
    session_config_fields = list(session_config_fields)

    participants = Participant.objects.filter(session=cursession).order_by('id').values()
    if not participants:
        # 1 empty row
        return [[]]

    session_fields = get_field_names_for_csv(Session)
    participant_fields = get_field_names_for_csv(Participant)
    participant_fields.append('payoff_plus_participation_fee')
    header_row = ['participant.{}'.format(fname) for fname in participant_fields]
    header_row += ['session.{}'.format(fname)
                   for fname in session_fields]
    header_row += ['session.config.{}'.format(fname)
                   for fname in session_config_fields]
    rows = [header_row]
    for participant in participants:
        session = cursession #session_cache[participant['session_id']]
        participant['payoff_plus_participation_fee'] = get_payoff_plus_participation_fee(session, participant)
        row = [sanitize_for_csv(participant[fname]) for fname in participant_fields]

        row += [sanitize_for_csv(getattr(session, fname)) for fname in session_fields]
        row += [sanitize_for_csv(session.config.get(fname)) for fname in session_config_fields]
        rows.append(row)

    # heuristic to get the most relevant order of apps
    app_sequences = collections.Counter()
    for session in sessions:
        # we loaded the config earlier
        app_sequence = session.config['app_sequence']
        app_sequences[tuple(app_sequence)] += session.num_participants
    most_common_app_sequence = app_sequences.most_common(1)[0][0]

    apps_not_in_popular_sequence = [
        app for app in settings.INSTALLED_OTREE_APPS
        if app not in most_common_app_sequence]

    order_of_apps = list(most_common_app_sequence) + apps_not_in_popular_sequence

    rounds_per_app = OrderedDict()
    for app_name in order_of_apps:
        models_module = get_models_module(app_name)
        agg_dict = models_module.Subsession.objects.all().aggregate(Max('round_number'))
        highest_round_number = agg_dict['round_number__max']

        if highest_round_number is not None:
            rounds_per_app[app_name] = highest_round_number
    for app_name in rounds_per_app:
        for round_number in range(1, rounds_per_app[app_name] + 1):
            new_rows = get_rows_for_wide_csv_round(app_name, round_number, sessions)
            for i in range(len(rows)):
                try:
                    rows[i].extend(new_rows[i])
                except:
                    ...
    return rows

def export_wide(fp, file_extension='csv', session_code=None):
    rows = get_rows_for_wide_csv(session_code=session_code)
    if file_extension == 'xlsx':
        _export_xlsx(fp, rows)
    else:
        _export_csv(fp, rows)
