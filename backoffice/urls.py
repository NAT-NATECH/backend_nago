from django.conf.urls import url
#project
from backoffice.views import *

urlpatterns = [
    url(r'^$', Home.as_view(), name='backoffice'),
    url(r'^personlist/$', PersonList.as_view(), name='PersonList'),
    url(r'^personcreate/$', PersonCreateModify.as_view(), name='PersonCreate'),
    url(r'^personmodify/(?P<pk>\d+)/$', PersonCreateModify.as_view(), name='PersonModify'),
    url(r'^persondeleteajax/$', PersonDeleteAjax.as_view(), name='PersonDeleteAjax'),


    url(r'^transactionsearch/$', TransactionSearch.as_view(), name='TransactionSearch'),
]
