from django.views.generic.base import View, TemplateResponseMixin


# TemplateView in Django 1.4 stuffs your context dict from get_context_data
# into a variable named 'params'.  Fix this by doing what >= 1.5 does.
class TemplateView(TemplateResponseMixin, View):

    """
    A view that renders a template. This view will also pass into the context
    any keyword arguments passed by the url conf.
    """
    def get_context_data(self, **kwargs):
        if 'view' not in kwargs:
            kwargs['view'] = self
        return kwargs

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)
