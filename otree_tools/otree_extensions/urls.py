from django.conf.urls import url, include

from otree_tools.views import *
from serializer_ext.views import DownloadJson

views_to_add = [
    # Trackers views:
    FocusEventList,
    FocusPerPageReport,
    EnterExitEventList,
    TempFileCSVExport,

    # Export views
    ListPVarsView,
    PVarsCSVExport,
    SpecificSessionDataView,
    DownloadJson,
    AllSessionsList,

]
urlpatterns = [url(i.url_pattern, i.as_view(), name=i.url_name) for i in views_to_add]
