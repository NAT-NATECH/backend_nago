from django.conf.urls import url
#project
from backoffice.views import *

urlpatterns = [
    url(r'^$', Home.as_view(), name='backoffice'),
]