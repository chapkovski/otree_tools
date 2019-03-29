from enum import Enum, unique
from otree_tools import cp


class ToolsEnum(Enum):
    @staticmethod
    def convert_name(n):
        return n.replace('_', ' ').lower().capitalize()

    @classmethod
    def as_tuple(cls):
        return [(c.value, cls.convert_name(c.name)) for c in cls]

    @classmethod
    def as_dict(cls):
        return {c.name: c.value for c in cls}

    @classmethod
    def values(cls):
        return [c.value for c in cls]


class ExitTypes(ToolsEnum):
    FORM_SUBMITTED = 0
    PAGE_UNLOADED = 1
    CLIENT_DISCONNECTED = 2


class FocusEnterEventTypes(ToolsEnum):
    PAGE_SHOWN = 0
    FOCUS_ON = 4


class FocusExitEventTypes(ToolsEnum):
    FOCUS_OFF = 2
    FORM_SUBMITTED = 5


EXITTYPES = ExitTypes.as_tuple()
FOCUS_ENTER_EVENT_TYPES = FocusEnterEventTypes.as_tuple()
FOCUS_EXIT_EVENT_TYPES = FocusExitEventTypes.as_tuple()
FOCUS_EVENT_TYPES = FOCUS_ENTER_EVENT_TYPES + FOCUS_EXIT_EVENT_TYPES
focus_exit_codes = FocusExitEventTypes.values()
focus_enter_codes = FocusEnterEventTypes.values()
WAITFORIMAGES_CHOICES = [(False, 'Before images are loaded'), (True, 'After images are loaded')]
