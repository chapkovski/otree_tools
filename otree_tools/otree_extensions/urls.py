from django.conf.urls import url, include

from otree_tools import views as v


urlpatterns = [url(v.ListPVarsView.url_pattern, v.ListPVarsView.as_view(),
                   name=v.ListPVarsView.url_name),
               url(v.PVarsCSVExport.url_pattern, v.PVarsCSVExport.as_view(),
                   name=v.PVarsCSVExport.url_name),
               ]
