from django.conf import settings
from django.template import loader
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.reverse import reverse


class CustomBrowsableAPIRenderer(BrowsableAPIRenderer):
    def get_filter_form(self, data, view, request):
        """
        Temporary patch a bug DRF, where it failed to "Infer if this is a list view or not"
        It did so by some hacky maneuver, which failed when a list view return error response (i.e. not 200)
        So here, instead of that, we just inspect `view.detail`
        """
        if not hasattr(view, 'get_queryset') or not hasattr(view, 'filter_backends'):
            return

        # Infer if this is a list view or not.
        if view.detail:
            return

        queryset = view.get_queryset()
        elements = []
        for backend in view.filter_backends:
            if hasattr(backend, 'to_html'):
                html = backend().to_html(request, queryset, view)
                if html:
                    elements.append(html)

        if not elements:
            return

        template = loader.get_template(self.filter_template)
        context = {'elements': elements}
        return template.render(context)

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        In production (DEBUG=False), only staff members are allowed to access Browsable API.
        (with DEBUG=True, everyone is still able to access)
        """
        if not settings.DEBUG:
            request = renderer_context['request']
            if not request.user.is_staff:
                url = reverse('rest_framework:login', request=request)
                return f'<a href="{url}">Login</a>'

        return super().render(data, accepted_media_type=accepted_media_type, renderer_context=renderer_context)
