from channels.routing import route_class
from .consumers import TimeTracker

channel_routing = [
    route_class(TimeTracker, path=TimeTracker.url_pattern),
]
