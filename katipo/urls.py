from django.conf.urls.defaults import *
from django.conf import settings

from models import Profile, Run, Url

urlpatterns = patterns('',
    (r'^$', 'django.views.generic.list_detail.object_list', {'queryset':Run.objects.all(), 'template_name':'home.html'}),
    
    url(r'^run/(?P<object_id>\d+)/$', 'katipo.views.run_detail', name="katipo-run-detail"),
    url(r'^run/(?P<run_id>\d+)/(?P<url>.*)$', 'katipo.views.url_detail', name="katipo-url-detail"),
    
    (r'^url/$', 'katipo.views.url_search'),
    (r'^url/(?P<url>.*)$', 'katipo.views.url_redirect'),
    
    (r'^profile/$', 'django.views.generic.list_detail.object_list', {'queryset':Profile.objects.all()}),
    url(r'^profile/(?P<object_id>\d+)/$', 'django.views.generic.create_update.update_object', {'model':Profile}, name="katipo-profile-detail"),
    (r'^profile/new/$', 'django.views.generic.create_update.create_object', {'model':Profile}),
    
    (r'^site_media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
)