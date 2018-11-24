from django.conf.urls import url, include

from otree_tools import views as v
from serializer_ext.views import DownloadJson

urlpatterns = [url(v.ListPVarsView.url_pattern, v.ListPVarsView.as_view(),
                   name=v.ListPVarsView.url_name),
               url(v.PVarsCSVExport.url_pattern, v.PVarsCSVExport.as_view(),
                   name=v.PVarsCSVExport.url_name),
               url(v.StreamingEnterCSV.url_pattern, v.StreamingEnterCSV.as_view(),
                   name=v.StreamingEnterCSV.url_name),
               url(v.AllSessionsList.url_pattern, v.AllSessionsList.as_view(),
                   name=v.AllSessionsList.url_name),
               url(v.FocusEventList.url_pattern, v.FocusEventList.as_view(),
                   name=v.FocusEventList.url_name),
               url(v.EnterExitEventList.url_pattern, v.EnterExitEventList.as_view(),
                   name=v.EnterExitEventList.url_name),
               url(r'^session_data/(?P<session_code>.*)/(?P<filetype>.*)/$', v.SpecificSessionDataView.as_view(),
                   name='session_data'),
               url(r'^download_json/(?P<session_code>\w+)$', DownloadJson.as_view(),
                   name='download_json'),
               url(v.StreamingFocusCSV.url_pattern, v.StreamingFocusCSV.as_view(),
                   name=v.StreamingFocusCSV.url_name),
               ]
