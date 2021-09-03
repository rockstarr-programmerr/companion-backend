import functools


def add_extra_action_urls(ViewSet):
    extra_actions = ViewSet.get_extra_actions()

    def update_response(method):
        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            response = method(self, *args, **kwargs)

            extra_action_urls = {}

            for action in extra_actions:
                url_name = action.url_name

                if self.detail and action.detail:
                    url = self.reverse_action(url_name, kwargs=kwargs)
                elif not self.detail and not action.detail:
                    url = self.reverse_action(url_name)
                else:
                    continue

                extra_action_urls[url_name] = url

            if not isinstance(response.data, dict):
                response.data = {'results': response.data}

            if not 'extra_action_urls' in response.data:
                response.data['extra_action_urls'] = extra_action_urls

            return response
        return wrapper

    if hasattr(ViewSet, 'list'):
        ViewSet.list = update_response(ViewSet.list)
    if hasattr(ViewSet, 'retrieve'):
        ViewSet.retrieve = update_response(ViewSet.retrieve)

    return ViewSet
