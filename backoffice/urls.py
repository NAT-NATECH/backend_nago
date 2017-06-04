from django.conf.urls import url
#project
from backoffice.views import *

urlpatterns = [
    url(r'^$', Home.as_view(), name='backoffice'),

    #USERS
    url(r'^userlist/$', UserList.as_view(), name='UserList'),
    url(r'^usercreate/$', UserCreateModify.as_view(), name='UserCreate'),
    url(r'^usermodify/(?P<pk>\d+)/$', UserCreateModify.as_view(), name='UserModify'),
    url(r'^userdeleteajax/$', UserDeleteAjax.as_view(), name='UserDeleteAjax'),
    url(r'^userfriendslist/(?P<pk>\d+)/$', UserFriendsList.as_view(), name='UserFriendsList'),

    #TRANSACTIONS
    url(r'^loanslist/$', LoansList.as_view(), name='LoansList'),
    url(r'^loanshow/(?P<pk>\d+)/$', LoansShow.as_view(), name='LoansShow'),

    url(r'^loansrequestlist/$', LoansRequestList.as_view(), name='LoansRequestList'),
    url(r'^loanrequestshow/(?P<pk>\d+)/$', LoansRequestShow.as_view(), name='LoansRequestShow'),

    url(r'^notificationlist/$', NotificationList.as_view(), name='NotificationList'),
    url(r'^notificationhow/(?P<pk>\d+)/$', NotificationShow.as_view(), name='NotificationShow'),
]
