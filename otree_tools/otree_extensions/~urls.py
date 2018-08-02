from django.conf.urls import url, include

from otree_tools import views as v


urlpatterns = [url(r'^session_data/(?P<session_code>.*)/(?P<filetype>.*)/$', v.SpecificSessionDataView.as_view(),
                   name='session_data'),
               url(r'^(?P<HITId>\w+)/',
                   include([
                       url(r'^assignments/$', v.AssignmentListView.as_view(), name='assignments_list'),
                       url(r'^delete/$', v.DeleteHitView.as_view(), name='delete_hit'),
                       url(r'^expire/', include([
                           url(r'^$', v.ExpireHitView.as_view(back_to_HIT=False), name='expire_hit'),
                           url(r'^back/$', v.ExpireHitView.as_view(back_to_HIT=True), name='expire_hit_back'),
                       ])),
                       url(r'^change_expiration/', include([
                           url(r'^$', v.UpdateExpirationView.as_view(back_to_HIT=False), name='change_expiration'),
                           url(r'^back/$', v.UpdateExpirationView.as_view(back_to_HIT=True), name='change_expiration_back'),
                       ])),
                   ])),
               url(r'^(?P<AssignmentID>\w+)/',
                   include([
                       url(r'^approve/$', v.ApproveAssignmentView.as_view(), name='approve_assignment'),
                       url(r'^reject/$', v.RejectAssignmentView.as_view(), name='reject_assignment'),
                       url(r'^send_message/$', v.SendMessageView.as_view(), name='send_message'),
                       url(r'^send_bonus/$', v.SendBonusView.as_view(), name='send_bonus'),
                   ])),
               ]
