from django.conf.urls import url, include

from otree_tools import views as v
from serializer_ext.views import DownloadJson

urlpatterns = [url(v.ListPVarsView.url_pattern, v.ListPVarsView.as_view(),
                   name=v.ListPVarsView.url_name),
               url(v.PVarsCSVExport.url_pattern, v.PVarsCSVExport.as_view(),
                   name=v.PVarsCSVExport.url_name),
               url(v.EnterExitCSVExport.url_pattern, v.EnterExitCSVExport.as_view(),
                   name=v.EnterExitCSVExport.url_name),
               url(v.FocusEventCSVExport.url_pattern, v.FocusEventCSVExport.as_view(),
                   name=v.FocusEventCSVExport.url_name),
               url(r'^session_data/(?P<session_code>.*)/(?P<filetype>.*)/$', v.SpecificSessionDataView.as_view(),
                   name='session_data'),
               url(r'^download_json/(?P<session_code>\w+)$', DownloadJson.as_view(),
                   name='download_json'),
               ]
