===============
django-starsweb
===============

A hosting app for the classic 4X space strategy game Stars_.

.. _Stars: http://en.wikipedia.org/wiki/Stars!


Requirements
------------
- Python 3.10+
- Django 5.0, 5.1, 5.2
- Markdown
- nh3
- django-sendfile2_
- starslib_

.. _django-sendfile2: https://codeberg.org/moggers87/django-sendfile2
.. _starslib: https://github.com/jbradberry/starslib


Recommended
-----------
- Wine
- Stars 2.60i / 2.70i
- django-turn-generation_
- django-micro-press_

.. _django-turn-generation: https://github.com/jbradberry/django-turn-generation
.. _djang-micro-press: https://github.com/jbradberry/django-micro-press


Installation
------------

Use pip to install django-starsweb from github
::

    pip install git+https://github.com/jbradberry/django-starsweb.git


Configuration
-------------

Add Starsweb to the ``INSTALLED_APPS`` in your settings file.
::

    INSTALLED_APPS = (
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.sites',
        'django.contrib.messages',
        'django.contrib.staticfiles',

        # Added.
        'starsweb',
    )

Configure Sendfile::

    SENDFILE_BACKEND = 'django_sendfile.backends.simple'
    SENDFILE_ROOT = MEDIA_ROOT = BASE_DIR / 'media'

Also, be sure to include ``starsweb.urls`` in your root urlconf.

Example::

    from django.urls import include, path

    urlpatterns = [
        path('', include('starsweb.urls')),
        path('admin/', include('admin.site.urls')),
        path('accounts/', include('django.contrib.auth.urls'),
    ]
