from urllib.parse import urlparse, unquote, urlencode, parse_qsl, ParseResult


def get_url_params(url):
    url = unquote(url)
    p_url = urlparse(url)
    p_qs = parse_qsl(p_url.query)
    p_params = dict(p_qs)
    return p_params


def update_url_params(url, new_params):
    url = unquote(url)
    p_url = urlparse(url)
    p_qs = parse_qsl(p_url.query)
    p_params = dict(p_qs)
    p_params.update(new_params)
    encoded_params = urlencode(p_params, doseq=True)

    new_url = ParseResult(
        p_url.scheme, p_url.netloc, p_url.path,
        p_url.params, encoded_params, p_url.fragment
    ).geturl()

    return new_url
