from django.conf.urls import url, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    url(r'^', include('server.urls')),
    ## Backoffice module's URLs
    url(r'^', include('backoffice.urls'), name='BackofficeApp'),
    ## Login/Loguot
    url(r'^accounts/login/$', auth_views.login, {'template_name': 'server/login.html'}, name ="loginBO"),
    url(r'^accounts/logout/$', auth_views.logout, {'next_page': '/accounts/login/'}, name ="logout")
]
