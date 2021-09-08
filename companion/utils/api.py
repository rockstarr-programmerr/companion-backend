import functools


def extra_action_urls(extra_actions_or_viewset):
    has_extra_actions = isinstance(extra_actions_or_viewset, dict)

    def decorator(ViewSet):
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

                if has_extra_actions:
                    extra = extra_actions_or_viewset
                    for key, value in extra.items():
                        extra[key] = self.request.build_absolute_uri(value)
                    extra_action_urls.update(extra_actions_or_viewset)

                if extra_action_urls:
                    response.data['extra_action_urls'] = extra_action_urls
                return response

            return wrapper

        if hasattr(ViewSet, 'list'):
            ViewSet.list = update_response(ViewSet.list)

        return ViewSet

    if has_extra_actions:
        return decorator
    else:
        return decorator(extra_actions_or_viewset)
