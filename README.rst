========================================================================
Set of tools facilitating the development of oTree projects
========================================================================


Installation:
***************
1. **Either**:

- type ``pip install otree_tools -U`` in your terminal window.
(`-U` or `--upgrade` key guarantees that if you already have `otree_tools` installed, it will update it to the most
recent version).


2. **or**:

-  clone exisiting project ``git clone https://github.com/otree-tools/otree_tools`` and copy the
``otree_tools`` folder into your project folder, next to the apps of your module.

3. After that add "otree_tools" to your EXTENSION_APPS section of ``settings.py`` file like this::

    EXTENSION_APPS = ['otree_tools']

If your settings contain other otree extensions, listed in EXTENSION_APSS, just add `otree_tools` into the same list.
The extensions work independently from each other and they will not be in a conflict.

4. If you would like to track time or focused/unfocused time a user spends on a specific page, you need to include
to a standard oTree template a reference to `otree_tools` and then include trackers::

     {% load otree otree_tools %}
     {% block content %}
        {% tracking_focus %}
        {% tracking_time %}
     {% endblock%}

`tracking_focus` and `tracking_time` tags can be included into any block, not necessarily to `content`

Version History
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

0.2.1: Incorporating parts of otree_custom_export: json export, and data export for specific sessions; export of focus and
enter/exit trackers as CSV

0.2.2: fixin issue with restframework

0.2.3: fixin issue with time_tracking tag

0.3.0: OtherField and MultipliChoice Field supports FOO_choices from oTree; admin menu; pagination of all lists
streaming export of time and focus trackers; issue with time tracker events is solved

0.3.1: Upgrading boto

0.3.2: Solving issue with Multiple Choice Field

0.3.3: in `utils` two extra functions are added: `get_focused_time()` and `get_unfocused_time()`

0.3.4: minor error correction in `get_focused_time` function

0.3.6: `confirm_button` tag for showing modal with confirmation before proceeding further

0.3.8: Fixing `get_XXX_time` functions

0.3.9: Converting `get_time_per_page` function making it return `.total_seconds()`, not a timedelta object

0.3.10: fixing error message in multipleselectfield

0.3.11: adding `min_choices` to multipleselectfield

0.3.12: minor fix of multipleselectfield - dynamic choices

0.3.13: adding `num_focus_events`, `num_visibility_events` functions into `utils`

0.3.14: removing botocore ref

0.3.15b: adding marker for time tracker

0.3.16b: fixing low db data retrieval in time tracker

1.0.0: Huge reshuffle of time tracker.

1.0.1: Now `tracking_time` tag can optionally get a parameter `wait_for_images`. By default it is set to `True`.
        If it is set to `False` then we'll register time when the page is shown to the player, but before all images
        are loaded.

1.0.2: Fixing cp issue

1.1.0: Total reshuffle of trackers

1.1.1: Minor change in exporting channel