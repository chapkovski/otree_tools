from django.db import models
from otree.models import Participant
from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

EXITTYPES = [(0, 'form submitted'), (1, 'page unloaded'), (2, 'client disconnected')]
FOCUS_EVENT_TYPES = (
    (0, 'Page shown'), (1, 'Visibility: off'), (2, 'Focus: off'), (3, 'Visibility: on'), (4, 'Focus: on'),
    (5, 'Form submitted'))
WAITFORIMAGES_CHOICES = [(False, 'Before images are loaded'), (True, 'After images are loaded')]
"""
There are 3 different scenarios how a client may exit the page.
1. He can submit the form by clicking next (or in oTree any other button because the entire page
is wrapped into form tags
2. He can refresh the page (clicking F5 or command+R)
3. The browser can be closed (by accident or intentionally)

The Db structure is the following:
Enter timestamp is linked to participant, and it also contains info on page. All timestamps correspond on time
when a participant connects to a channel on page load.

since there are several exit timestamp events that can be linked to one single enter event, that means that they
should be connected to an enter timestamp via ForeignKey.
How the connection takes place:
The Enter event has  a boolean attribute Closed, initially set to false.
When the client disconnects it looks for all not closed enter events for this participant-page pair, and closes them
As a safeguard, the same closing happens everytime a client connects to the page, and before a new open Enter event is
created.

The aggregation for stats purposes is done the following way:
* we choose all enter events for the specific participant and page
* collect the earliest exit event for each enter event (via subquery and aggregation)
* annotate the query via F and ExpressionWrapper to calculate the difference between this earlist exit and its parent
Enter event
...
PROFIT!!
"""


class GeneralEvent(models.Model):
    class Meta:
        get_latest_by = 'timestamp'
        abstract = True

    page_name = models.CharField(max_length=1000)
    participant = models.ForeignKey(to=Participant, related_name="%(app_label)s_%(class)s_events")
    app_name = models.CharField(max_length=1000)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    player_id = models.PositiveIntegerField()
    player = GenericForeignKey('content_type', 'player_id')
    timestamp = models.DateTimeField()


class Enter(GeneralEvent):
    wait_for_images = models.BooleanField(choices=WAITFORIMAGES_CHOICES, default=True)

    def __str__(self):
        return f'id: {self.pk}, Enter: {self.page_name}; time: {self.timestamp}'


class Exit(GeneralEvent):
    enter = models.OneToOneField(to='Enter', related_name='exit', null=True)
    timestamp = models.DateTimeField()
    exit_type = models.IntegerField(choices=EXITTYPES)

    def __str__(self):
        return f'id: {self.pk}, Exit: {self.page_name}; time: {self.timestamp}; Type: {self.get_exit_type_display()} '


class FocusEvent(GeneralEvent):
    event_desc_type = models.CharField(max_length=1000)
    event_num_type = models.IntegerField(choices=FOCUS_EVENT_TYPES)
