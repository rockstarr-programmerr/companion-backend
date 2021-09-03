from rest_framework import serializers


class _ExtraActionUrlsMixin:
    def get_extra_action_urls(self, obj, is_detail):
        view = self.context['view']
        actions = view.get_extra_actions()

        urls = {}
        for action in actions:
            url_name = action.url_name

            if action.detail and is_detail:
                url = view.reverse_action(url_name, kwargs={'pk': obj.pk})
            elif not action.detail and not is_detail:
                url = view.reverse_action(url_name)
            else:
                continue

            url_name = url_name.replace('-', '_')
            urls[url_name] = url

        return urls


class ExtraListActionUrlsMixin(_ExtraActionUrlsMixin):
    def get_extra_action_urls(self, obj):
        return super().get_extra_action_urls(obj, False)



class ExtraDetailActionUrlsMixin(_ExtraActionUrlsMixin):
    def get_extra_action_urls(self, obj):
        return super().get_extra_action_urls(obj, True)
