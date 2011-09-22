from django.conf.urls.defaults import *


urlpatterns = patterns('starsweb.views',
    (r'^games/$', 'game_list'),
    (r'^games/(?P<slug>[-\w]+)/$', 'game_detail'),
    (r'^games/(?P<gameslug>[-\w]+)/race/(?P<slug>[-\w]+)/$', 'race_detail'),
)
