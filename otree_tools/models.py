from django.db import models
from otree.models import Participant
from django.db import transaction

EXITTYPES = [(0, 'form submitted'), (1, 'page unloaded'), (2, 'client disconnected')]


# There are 3 different scenarios how a client may exit the page.
# 1. He can submit the form by clicking next (or in oTree any other button because the entire page
# is wrapped into form tags
# 2. He can refresh the page (clicking F5 or command+R)
# 3. The browser can be closed (by accident or intentionally)

# The Db structure is the following:
# Enter timestamp is linked to participant, and it also contains info on page. All timestamps correspond on time
# when a participant connects to a channel on page load.

# since there are several exit timestamp events that can be linked to one single enter event, that means that they
# should be connected to an enter timestamp via ForeignKey.
# How the connection takes place:
# The Enter event has  a boolean attribute Closed, initially set to false.
# When the client disconnects it looks for all not closed enter events for this participant-page pair, and closes them
# As a safeguard, the same closing happens everytime a client connects to the page, and before a new open Enter event is
# created.

# The aggregation for stats purposes is done the following way:
# * we choose all enter events for the specific participant and page
# * collect the earliest exit event for each enter event (via subquery and aggregation)
# * annotate the query via F and ExpressionWrapper to calculate the difference between this earlist exit and its parent
# Enter event
# ...
# PROFIT!!
class OpenEnterEventManager(models.Manager):

    def get_queryset(self):
        return super().get_queryset().filter(closed=False)

    def close_all(self, participant, page_name):
        q = self.get_queryset().filter(participant=participant, page_name=page_name)
        q.update(closed=True)


# TODO: move ListField as a separate ModelField for storing lists
class EnterEvent(models.Model):
    class Meta:
        get_latest_by = 'timestamp'
        base_manager_name = 'objects'

    objects = models.Manager()
    opened = OpenEnterEventManager()
    page_name = models.CharField(max_length=1000)
    participant = models.ForeignKey(to=Participant, related_name='enters')
    timestamp = models.DateTimeField()
    closed = models.BooleanField(default=False)
    closed_at = models.DateTimeField(null=True)
    def __str__(self):
        return 'id: {}, Enter: {}; time: {}; closed: {}'.format(self.pk, self.page_name, self.timestamp, self.closed)


class ExitEvent(models.Model):
    class Meta:
        get_latest_by = 'timestamp'

    enter_event = models.ForeignKey(to=EnterEvent, related_name='exits')
    timestamp = models.DateTimeField()
    exit_type = models.IntegerField(choices=EXITTYPES)

    def __str__(self):
        return 'id: {}, time: {}; for ENRANCE event {}. Type: {} '.format(self.pk,
                                                                          self.timestamp,
                                                                          self.enter_event.timestamp,
                                                                          self.get_exit_type_display())
