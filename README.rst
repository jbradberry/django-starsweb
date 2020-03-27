===============
django-starsweb
===============

.. image:: https://travis-ci.com/jbradberry/django-starsweb.svg?branch=master
    :target: https://travis-ci.com/jbradberry/django-starsweb

A hosting app for the classic 4X space strategy game Stars_.

.. _Stars: http://en.wikipedia.org/wiki/Stars!


Requirements
------------
- Python 2.7, 3.5+
- Django >= 1.10, < 2.3
- django-sendfile2_
- django-template-utils_
- lxml
- starslib

.. _django-sendfile2: https://github.com/moggers87/django-sendfile2
.. _django-template-utils: https://bitbucket.org/ubernostrum/django-template-utils


Recommended
-----------
- django-micro-press


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

Also, be sure to include ``starsweb.urls`` in your root urlconf.

Example::

    from django.conf.urls import include, url

    urlpatterns = [
        url(r'^', include('starsweb.urls')),
        url(r'^admin/', include('admin.site.urls')),
        url(r'^accounts/', include('django.contrib.auth.urls'),
    ]
