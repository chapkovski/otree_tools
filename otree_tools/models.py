from django.db import models
from otree.models import Participant

EXITTYPES = [(0, 'form submitted'), (1, 'page refreshed'), (2, 'client disconnected')]
# There are 3 different scenarios how a client may exit the page.
# 1. He can submit the form by clicking next (or in oTree any other button because the entire page
# is wrapped into form tags
# 2. He can refresh the page (clicking F5 or command+R)
# 3. The browser can be closed (by accident or intentionally)

# TODO: move ListField as a separate ModelField for storing lists
class TimeStamp(models.Model):
    page_name = models.CharField(max_length=1000)
    participant = models.ForeignKey(to=Participant, related_name='timestamps')
    enter_time = models.DateTimeField()
    exit_time = models.DateTimeField()
    exit_type = models.CharField(max_length=1000, choices=EXITTYPES)

