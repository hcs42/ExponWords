from django.conf.urls.defaults import *

urlpatterns = patterns('ew.views',
    (r'^$', 'index'),
    #(r'^(?P<poll_id>\d+)/$', 'menu'),
    #(r'^(?P<poll_id>\d+)/results/$', 'results'),
    #(r'^(?P<poll_id>\d+)/vote/$', 'vote'),
    #(r'^login/$', 'django.contrib.auth.views.login'),
    #(r'^logout/$', 'django.contrib.auth.views.logout', {'next_page':'../login'}),
)
