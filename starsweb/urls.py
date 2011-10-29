from django.conf.urls.defaults import *
from django.conf import settings


urlpatterns = patterns('starsweb.views',
    url(r'^new-game/$', 'create_game', name='starsweb_create_game'),
    url(r'^games/$', 'game_list', name='starsweb_game_list'),
    url(r'^games/(?P<slug>[-\w]+)/$', 'game_detail', name='starsweb_game_detail'),
    url(r'^games/(?P<gameslug>[-\w]+)/race/(?P<slug>[-\w]+)/$', 'race_detail', name='starsweb_race_detail'),
)

if 'micropress' in settings.INSTALLED_APPS:
    # optional django-micro-press
    urlpatterns += patterns('',
        (r'^games/(?P<realm_slug>[-\w]+)/news/',
         include('micropress.urls', namespace="starsweb", app_name="micropress"),
         {'realm_content_type': 'starsweb.Game'}),
    )
