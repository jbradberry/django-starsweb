from django.conf import settings

import markdown
import nh3


MARKUP_FILTER_OPTS = getattr(settings, 'MARKUP_FILTER_OPTS', {})


def process(html):
    html = markdown.markdown(html)
    if html:
        return nh3.clean(html, **MARKUP_FILTER_OPTS)
    return ''
