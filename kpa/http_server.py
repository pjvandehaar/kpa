

def status_code_server(environ, start_response):
    # TODO: query all status codes using [urllib.request.urlopen, requests.get, requests.get.raise_for_status] to compare error-handling
    #  - results should be: (urlopen / requests.get*)
    #    - can't connect => URLError / requests.exceptions.ConnectionError
    #    - 000-100 => BadStatusLine / requests.exceptions.ConnectionError
    #    - 101-199 => HTTPError / ok
    #    - 200-299 => ok
    #    - 301-303,307 with valid "Location:" header => respond for new location
    #    - 300-399 otherwise => HTTPError / ok
    #    - 400-599 => HTTPError / ok (but raise_for_status raises requests.exceptions.HTTPError)
    #    - 600-999 => HTTPError / ok
    import re
    headers = [('Content-type', 'text/plain')]
    path = environ.get('PATH_INFO','')

    m = re.match(r'^/([0-9]{3})/([0-9]{3})$', path)
    if m:
        status = m.group(1) + ' WAT'
        headers.append(('Location', '/{}'.format(m.group(2))))
        ret = 'following xxx -> xxx path for {}\n'.format(path)
        start_response(status, headers); return [ret.encode('utf8')]

    m = re.match(r'^/([0-9]{3})$', path)
    if m:
        status = m.group(1) + ' WAT'
        ret = 'following xxx path for {}\n'.format(path)
        start_response(status, headers); return [ret.encode('utf8')]

    raise Exception(f'bad url: {path}')


def serve(app):
    from .http_utils import run_gunicorn
    try:
        run_gunicorn(app)
    except KeyboardInterrupt:
        pass
