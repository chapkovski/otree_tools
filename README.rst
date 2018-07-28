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