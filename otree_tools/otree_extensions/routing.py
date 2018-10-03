from channels.routing import route_class
from .consumers import TimeTracker, FocusTracker


channel_routing = [
    route_class(TimeTracker, path=TimeTracker.url_pattern, ),
    route_class(FocusTracker, path=FocusTracker.url_pattern, ),
]
