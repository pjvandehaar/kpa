

def status_code_app(environ, start_response):
    # TODO: use werkzeug
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


def serve():
    from .http_utils import run_gunicorn
    try:
        run_gunicorn(status_code_app)
    except KeyboardInterrupt:
        pass
