import markdown
from django.conf import settings


MARKUP_FILTER_OPTS = getattr(settings, 'MARKUP_FILTER_OPTS', {})


def process(html):
    html = markdown.markdown(html)
    if html:
        # FIXME: use a new html cleaner, probably nh3
        return html
    return u''
