
from django.conf import settings
from django.urls import include, re_path, reverse_lazy
from django.views.generic import RedirectView

from . import views


urlpatterns = [
    re_path(r'^$', RedirectView.as_view(url=reverse_lazy('game_list'), permanent=False)),
    re_path(r'^user/$', views.UserDashboard.as_view(), name='user_dashboard'),
    re_path(r'^user/download/(?P<pk>\d+)/$', views.UserRaceDownload.as_view(), name='userrace_download'),
    re_path(r'^user/upload/(?P<pk>\d+)/$', views.UserRaceUpload.as_view(), name='userrace_upload'),
    re_path(r'^user/create/$', views.UserRaceCreate.as_view(), name='userrace_create'),
    re_path(r'^user/update/(?P<pk>\d+)/$', views.UserRaceUpdate.as_view(), name='userrace_update'),
    re_path(r'^user/delete/(?P<pk>\d+)/$', views.UserRaceDelete.as_view(), name='userrace_delete'),
    re_path(r'^create/$', views.GameCreateView.as_view(), name='create_game'),
    re_path(r'^game/$', views.GameListView.as_view(), name='game_list'),
    re_path(r'^game/(?P<slug>[-\w]+)/$', views.GameDetailView.as_view(), name='game_detail'),
    re_path(r'^game/(?P<game_slug>[-\w]+)/admin/$', views.GameAdminView.as_view(), name='game_admin'),
    re_path(r'^game/(?P<game_slug>[-\w]+)/join/$', views.GameJoinView.as_view(), name='game_join'),
    re_path(r'^game/(?P<game_slug>[-\w]+)/download/$', views.GameMapDownload.as_view(), name='game_mapdownload'),
    re_path(r'^game/(?P<slug>[-\w]+)/score/$', views.ScoreGraphView.as_view(), name='score_graph'),
    re_path(r'^game/(?P<game_slug>[-\w]+)/race/(?P<race_slug>[-\w]+)/pages/$', views.RacePageView.as_view(),
            {'slug': None}, name='race_homepage'),
    re_path(r'^game/(?P<game_slug>[-\w]+)/race/(?P<race_slug>[-\w]+)/pages/(?P<slug>[-\w]+)/$',
            views.RacePageView.as_view(), name='race_page'),
    re_path(r'^game/(?P<game_slug>[-\w]+)/race/(?P<race_slug>[-\w]+)/create-page/$',
            views.RacePageCreate.as_view(), name='race_page_create'),
    re_path(r'^game/(?P<game_slug>[-\w]+)/race/(?P<race_slug>[-\w]+)/update-page/(?P<slug>[-\w]+)/$',
            views.RacePageUpdate.as_view(), name='race_page_update'),
    re_path(r'^game/(?P<game_slug>[-\w]+)/race/(?P<race_slug>[-\w]+)/delete-page/(?P<slug>[-\w]+)/$',
            views.RacePageDelete.as_view(), name='race_page_delete'),
    re_path(r'^game/(?P<game_slug>[-\w]+)/race/(?P<race_slug>[-\w]+)/manage/$',
            views.RaceDashboardView.as_view(), name='race_dashboard'),
    re_path(r'^game/(?P<game_slug>[-\w]+)/race/(?P<race_slug>[-\w]+)/edit/$',
            views.RaceUpdateView.as_view(), name='race_update'),
    re_path(r'^game/(?P<game_slug>[-\w]+)/race/(?P<race_slug>[-\w]+)/ambassador/$',
            views.AmbassadorUpdateView.as_view(), name='ambassador_update'),
    re_path(r'^game/(?P<game_slug>[-\w]+)/race/(?P<race_slug>[-\w]+)/upload/$',
            views.RaceFileUpload.as_view(), name='race_upload'),
    re_path(r'^game/(?P<game_slug>[-\w]+)/race/(?P<race_slug>[-\w]+)/download/$',
            views.RaceFileDownload.as_view(), name='race_download'),
    re_path(r'^game/(?P<game_slug>[-\w]+)/race/(?P<race_slug>[-\w]+)/bind/$',
            views.RaceFileBind.as_view(), name='race_bind'),
    re_path(r'^game/(?P<game_slug>[-\w]+)/turn/(?P<race_slug>[-\w]+)/download/$',
            views.StateFileDownload.as_view(), name='state_download'),
    re_path(r'^game/(?P<game_slug>[-\w]+)/orders/(?P<race_slug>[-\w]+)/download/$',
            views.OrderFileDownload.as_view(), name='orders_download'),
    re_path(r'^game/(?P<game_slug>[-\w]+)/orders/(?P<race_slug>[-\w]+)/upload/$',
            views.OrderFileUpload.as_view(), name='orders_upload'),
    re_path(r'^game/(?P<game_slug>[-\w]+)/history/(?P<race_slug>[-\w]+)/download/$',
            views.HistoryFileDownload.as_view(), name='history_download'),
    re_path(r'^game/(?P<game_slug>[-\w]+)/history/(?P<race_slug>[-\w]+)/upload/$',
            views.HistoryFileUpload.as_view(), name='history_upload'),
]

if 'micropress' in settings.INSTALLED_APPS:
    # optional django-micro-press
    urlpatterns += [
        re_path(r'^game/(?P<realm_slug>[-\w]+)/news/', include('micropress.urls', namespace="starsweb", app_name="micropress"),
                {'realm_content_type': 'starsweb.Game'}),
    ]
