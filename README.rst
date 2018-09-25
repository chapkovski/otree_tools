========================================================================
Set of tools facilitating the development of oTree projects
========================================================================

Author: Philipp Chapkovski (chapkovski@gmail.com)

Installation:
***************
1. **Either**:

- type ``pip install otree_tools`` in your terminal window.


2. **or**:

-  clone exisiting project ``git clone https://github.com/chapkovski/otree_tools`` and copy the
``otree_tools`` folder into your project folder, next to the apps of your module.

3. After that add "otree_tools" to your INSTALLED_APPS section of ``settings.py`` file like this::

    INSTALLED_APPS = [
        'otree',
        'otree_tools',
    ]



## Version History
***************

0.0.4: An `AdvancedSliderWidget` is added to `widgets`
0.0.5: An `AdvancedSliderWidget` is updated to work with float numbers
0.0.6: An `AdvancedSliderWidget` has a new option 'suffix' which is added to each label
0.0.7: `ListField` is added as a possible field to render multiple choice selector
0.0.8: Temporarily removing static jquery-ui files
0.0.9: ListField gets options to set initial/default values
0.0.10: ListField gets an option  `max_choices`
0.0.11: New tag `{% tracking_time %}` is added that allows to measure precisely time spent per page
0.0.12: `ListField` renamed to `MultipleChoiceModelField`. `ListField` becomes a general field to store lists
0.0.13: `{% tracking_focus}` tag - to track when/if user switches to another tab while staying on the page
0.0.14: Fixing issue with `{% tracking_focus}` tag - initial visibility event is registered now
0.0.15: Minor fixes with trackers
0.1.0: Export of participant.vars is added
0.1.1: Hosting of Anton Shurashov radiogrid widget (https://github.com/Sinkler/django-radiogrid)
