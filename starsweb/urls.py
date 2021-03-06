from __future__ import absolute_import

from django.conf import settings
from django.conf.urls import url, include
from django.urls import reverse_lazy
from django.views.generic import RedirectView

from . import views


urlpatterns = [
    url(r'^$', RedirectView.as_view(url=reverse_lazy('game_list'), permanent=False)),
    url(r'^user/$', views.UserDashboard.as_view(),
        name='user_dashboard'),
    url(r'^user/download/(?P<pk>\d+)/$', views.UserRaceDownload.as_view(),
        name='userrace_download'),
    url(r'^user/upload/(?P<pk>\d+)/$', views.UserRaceUpload.as_view(),
        name='userrace_upload'),
    url(r'^user/create/$', views.UserRaceCreate.as_view(),
        name='userrace_create'),
    url(r'^user/update/(?P<pk>\d+)/$', views.UserRaceUpdate.as_view(),
        name='userrace_update'),
    url(r'^user/delete/(?P<pk>\d+)/$', views.UserRaceDelete.as_view(),
        name='userrace_delete'),
    url(r'^create/$', views.GameCreateView.as_view(), name='create_game'),
    url(r'^game/$', views.GameListView.as_view(), name='game_list'),
    url(r'^game/(?P<slug>[-\w]+)/$', views.GameDetailView.as_view(),
        name='game_detail'),
    url(r'^game/(?P<game_slug>[-\w]+)/admin/$', views.GameAdminView.as_view(),
        name='game_admin'),
    url(r'^game/(?P<game_slug>[-\w]+)/join/$', views.GameJoinView.as_view(),
        name='game_join'),
    url(r'^game/(?P<game_slug>[-\w]+)/download/$', views.GameMapDownload.as_view(),
        name='game_mapdownload'),
    url(r'^game/(?P<slug>[-\w]+)/score/$',
        views.ScoreGraphView.as_view(), name='score_graph'),
    url(r'^game/(?P<game_slug>[-\w]+)/race/(?P<race_slug>[-\w]+)/pages/$',
        views.RacePageView.as_view(), {'slug': None}, name='race_homepage'),
    url(r'^game/(?P<game_slug>[-\w]+)/race/(?P<race_slug>[-\w]+)/pages/(?P<slug>[-\w]+)/$',
        views.RacePageView.as_view(), name='race_page'),
    url(r'^game/(?P<game_slug>[-\w]+)/race/(?P<race_slug>[-\w]+)/create-page/$',
        views.RacePageCreate.as_view(), name='race_page_create'),
    url(r'^game/(?P<game_slug>[-\w]+)/race/(?P<race_slug>[-\w]+)/update-page/(?P<slug>[-\w]+)/$',
        views.RacePageUpdate.as_view(), name='race_page_update'),
    url(r'^game/(?P<game_slug>[-\w]+)/race/(?P<race_slug>[-\w]+)/delete-page/(?P<slug>[-\w]+)/$',
        views.RacePageDelete.as_view(), name='race_page_delete'),
    url(r'^game/(?P<game_slug>[-\w]+)/race/(?P<race_slug>[-\w]+)/manage/$',
        views.RaceDashboardView.as_view(), name='race_dashboard'),
    url(r'^game/(?P<game_slug>[-\w]+)/race/(?P<race_slug>[-\w]+)/edit/$',
        views.RaceUpdateView.as_view(), name='race_update'),
    url(r'^game/(?P<game_slug>[-\w]+)/race/(?P<race_slug>[-\w]+)/ambassador/$',
        views.AmbassadorUpdateView.as_view(), name='ambassador_update'),
    url(r'^game/(?P<game_slug>[-\w]+)/race/(?P<race_slug>[-\w]+)/upload/$',
        views.RaceFileUpload.as_view(), name='race_upload'),
    url(r'^game/(?P<game_slug>[-\w]+)/race/(?P<race_slug>[-\w]+)/download/$',
        views.RaceFileDownload.as_view(), name='race_download'),
    url(r'^game/(?P<game_slug>[-\w]+)/race/(?P<race_slug>[-\w]+)/bind/$',
        views.RaceFileBind.as_view(), name='race_bind'),
    url(r'^game/(?P<game_slug>[-\w]+)/turn/(?P<race_slug>[-\w]+)/download/$',
        views.StateFileDownload.as_view(), name='state_download'),
    url(r'^game/(?P<game_slug>[-\w]+)/orders/(?P<race_slug>[-\w]+)/download/$',
        views.OrderFileDownload.as_view(), name='orders_download'),
    url(r'^game/(?P<game_slug>[-\w]+)/orders/(?P<race_slug>[-\w]+)/upload/$',
        views.OrderFileUpload.as_view(), name='orders_upload'),
    url(r'^game/(?P<game_slug>[-\w]+)/history/(?P<race_slug>[-\w]+)/download/$',
        views.HistoryFileDownload.as_view(), name='history_download'),
    url(r'^game/(?P<game_slug>[-\w]+)/history/(?P<race_slug>[-\w]+)/upload/$',
        views.HistoryFileUpload.as_view(), name='history_upload'),
]

if 'micropress' in settings.INSTALLED_APPS:
    # optional django-micro-press
    urlpatterns += [
        (r'^game/(?P<realm_slug>[-\w]+)/news/',
         include('micropress.urls', namespace="starsweb",
                 app_name="micropress"),
         {'realm_content_type': 'starsweb.Game'}),
    ]
