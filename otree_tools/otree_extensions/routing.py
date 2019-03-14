from channels.routing import route_class
from .consumers import TimeTracker, FocusTracker

trackers = [TimeTracker, FocusTracker]
channel_routing = [route_class(i, path=i.url_pattern, ) for i in trackers]
