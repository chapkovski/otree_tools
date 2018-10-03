from rest_framework import serializers
from otree.models.subsession import BaseSubsession
from otree.models.group import BaseGroup
from otree.models.player import BasePlayer
from otree.models import Session, Participant

# we filter out these 'technical' fields.
block_fields = ['_gbat_arrived', '_gbat_grouped', '_index_in_subsessions', '_index_in_pages', '_index_in_pages',
                '_waiting_for_ids', '_last_page_timestamp', '_last_request_timestamp', 'is_on_wait_page',
                '_current_page_name', '_current_app_name', '_round_number', '_current_form_page_url', '_max_page_index',
                '_browser_bot_finished', '_pre_create_id', '_admin_report_app_names', '_admin_report_num_rounds',
                '_anonymous_code']


class oTreeSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ['pk', ]

    def build_serializer(self, class_name, related_model, base_serializer):
        class NestedSerializer(oTreeSerializer):
            class Meta:
                model = related_model
                fields = '__all__'

        field_class = type(class_name, (NestedSerializer, base_serializer), {})
        return field_class

    def get_field_names(self, declared_fields, info):
        # we filter out all related models not to be in an everlasting loop. We add some of them back in
        # get_deeper_models later
        names = [f.name for f in self.Meta.model._meta.get_fields() if not f.related_model]
        res = list(super().get_field_names(declared_fields, info))
        res += names
        res = [r for r in res if r not in block_fields]
        return res

    def get_deeper_models(self):
        return

    def __init__(self, *args, **kwargs):
        # I am not sure it's an optimal solution but looks like a compact one right now
        model = kwargs.pop('model', None)
        if model:
            self.Meta.model = model
        super().__init__(*args, **kwargs)

    def get_fields(self):
        fields = super().get_fields()
        deeper = self.get_deeper_models()
        # here we look if there are some extra models to add. If yes, we are looping through all fields available
        # in the model with the fitting parent type. the 'field_name' is needed only for Subssession calling for
        # Group model (because there the related name has a naming convention not 'APP_MODEL' but simply 'group_set'
        if deeper:
            fff = self.Meta.model._meta.get_fields()
            for f in fff:
                if f.related_model:
                    if f.related_model.__base__ is deeper['base']:
                        if deeper.get('field_name'):
                            fname = deeper['field_name']
                        else:
                            fname = f.name
                        fields[fname] = self.build_serializer(class_name='serializer_{}'.format(fname),
                                                              related_model=f.related_model,
                                                              base_serializer=deeper['serializer'])(many=True)
        return fields


class PlayerSerializer(oTreeSerializer):
    class Meta:
        fields = ['pk', 'group', 'subsession']


class GroupSerializer(oTreeSerializer):
    ...


class ParticipantSerializer(oTreeSerializer):
    def get_deeper_models(self):
        return {
            'base': BasePlayer,
            'serializer': PlayerSerializer

        }

    class Meta:
        model = Participant


class SubSessionSerializer(oTreeSerializer):
    class Meta:
        fields = ()

    def get_deeper_models(self):
        return {
            'base': BaseGroup,
            'serializer': GroupSerializer,
            'field_name': 'group_set',
        }


class SessionSerializer(oTreeSerializer):
    participant_set = ParticipantSerializer(many=True)

    class Meta:
        model = Session
        fields = ('id', 'is_demo', 'num_participants', 'code', 'vars',
                  'participant_set',
                  )

    def get_deeper_models(self):
        return {
            'base': BaseSubsession,
            'serializer': SubSessionSerializer

        }
