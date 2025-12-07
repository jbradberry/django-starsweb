from __future__ import absolute_import
from lxml.html.clean import clean_html
import markdown
from django.conf import settings
import six


MARKUP_FILTER_OPTS = getattr(settings, 'MARKUP_FILTER_OPTS', {})
LXML_CLEAN_OPTS = getattr(settings, 'LXML_CLEAN_OPTS', {})


def process(html):
    html = markdown.markdown(html)
    if html:
        return clean_html(html, **LXML_CLEAN_OPTS)
    return u''
