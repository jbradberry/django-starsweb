from django.urls import include, path


urlpatterns = [
    path('', include('starsweb.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
]
