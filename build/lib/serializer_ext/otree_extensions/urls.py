from django.conf.urls import url, include
from serializer_ext import views as v
from django.conf import settings
from django.contrib.auth.decorators import login_required

urlpatterns = [
    url(r'^download_json/(?P<session_code>\w+)/(?P<random_code>\w+)/$', v.DownloadJson.as_view(), name='download_json'),
]

