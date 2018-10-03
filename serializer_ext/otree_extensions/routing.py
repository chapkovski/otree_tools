from channels.routing import route_class
from .consumers import JsonLoader

channel_routing = [
    route_class(JsonLoader, path=JsonLoader.url_pattern),

]
