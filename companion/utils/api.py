import functools


def extra_action_urls(ViewSet):
    extra_actions = ViewSet.get_extra_actions()

    def update_response(method):
        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            response = method(self, *args, **kwargs)
            if self.detail:  # Only care about list view
                return response

            extra_action_urls = {}

            for action in extra_actions:
                if action.detail:
                    continue

                url_name = action.url_name
                url = self.reverse_action(url_name)

                key = url_name.replace('-', '_')
                extra_action_urls[key] = url

            if not isinstance(response.data, dict):
                response.data = {'results': response.data}

            if extra_action_urls:
                response.data['extra_action_urls'] = extra_action_urls
            return response

        return wrapper

    if hasattr(ViewSet, 'list'):
        ViewSet.list = update_response(ViewSet.list)

    return ViewSet