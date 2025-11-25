
from .func_cache_utils import shelve_cache

from pathlib import Path
import json, shelve, time, datetime
from typing import Any, TypedDict

HTTP_Response = TypedDict('HTTP_Response', {
    'status_code': int,
    'headers': dict[str, str],
    'text': str,
})


def get(url:str, user_agent:str|None=None, raise_for_status:bool=True, validate_json:bool=False, log:bool=True, log_dir_label:str='default', use_cache:bool=False, cache_max_age:float|None=None) -> HTTP_Response:
    ## Q: This returns str, but maybe it should support bytes?  Eg, for a jpg/pdf
    import requests
    headers = {
        'User-Agent': user_agent or 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:62.0) Gecko/20100101 Firefox/62.0',
    }

    cache_filepath = Path('/tmp/kpa-request-cache') / (log_dir_label + '.shelve')
    cache_key = json.dumps([url, user_agent], separators=(',', ':'))
    log_filepath = Path('/tmp/kpa-request-logs') / log_dir_label / (get_datetime_digits() + '-' + url.replace('/', '%') + '.log')

    if use_cache:
        cache_filepath.parent.mkdir(exist_ok=True, parents=True)
        with shelve.open(str(cache_filepath)) as cache:
            if cache_key in cache:
                cached_timestamp, cached_http_response = cache[cache_key]
                if not cache_max_age or time.time() - cached_timestamp < cache_max_age:
                    assert isinstance(cached_http_response, dict)
                    assert isinstance(cached_http_response['status_code'], int)
                    assert isinstance(cached_http_response['headers'], dict)
                    assert isinstance(cached_http_response['text'], str)
                    return cached_http_response
    if log:
        log_filepath.parent.mkdir(exist_ok=True, parents=True)
        log_data = {
            'url': url,
            'headers': headers,
            'datetime': datetime.datetime.now().isoformat(),
        }
        log_filepath.write_text(json.dumps(log_data, indent=2))
    resp = requests.get(url, headers=headers)
    if log:
        log_data['resp'] = {
            'status_code': resp.status_code,
            'headers': dict(resp.headers),
            'text': resp.text,
        }
        log_filepath.write_text(json.dumps(log_data, indent=2))
    if raise_for_status:
        resp.raise_for_status()
    if validate_json:
        json.loads(resp.text)
    if use_cache and resp.status_code == 200:
        with shelve.open(str(cache_filepath)) as cache:
            cache[cache_key] = (time.time(), {
                'status_code': resp.status_code,
                'headers': dict(resp.headers),
                'text': resp.text,
            })
    return HTTP_Response({
        'status_code': resp.status_code,
        'headers': dict(resp.headers),
        'text': resp.text,
    })

def get_json(url:str, user_agent:str|None=None, raise_for_status:bool=True, log:bool=True, log_dir_label:str='default', use_cache:bool=False, cache_max_age:float|None=None) -> Any:
    resp = get(url, user_agent=user_agent, raise_for_status=raise_for_status, validate_json=True, log=log, log_dir_label=log_dir_label, use_cache=use_cache, cache_max_age=cache_max_age)
    return json.loads(resp['text'])



def get_datetime_digits():
    import datetime
    return datetime.datetime.now().strftime('%Y%m%d%H%M%S')

def get_ip():
    import subprocess
    return subprocess.check_output('dig +short myip.opendns.com @resolver1.opendns.com'.split()).strip().decode('ascii')
    # import socket
    # sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # sock.connect(('resolver1.opendns.com', 53))
    # sock.send(b'\0\0\1\0\0\1\0\0\0\0\0\0\4myip\7opendns\3com\0\0\1\0\1')
    # resp = sock.recv(1000)
    # return '.'.join(str(b) for b in resp[-4:])
    # import requests, re
    # data = requests.get('http://checkip.dyndns.com/').text
    # return re.compile(r'Address: (\d+\.\d+\.\d+\.\d+)').search(data).group(1)


def open_browser(url):
    import os
    import webbrowser
    if 'DISPLAY' not in os.environ:
        print('The DISPLAY variable is not set, so not attempting to open a web browser\n')
        return False
    for name in 'windows-default macosx chrome chromium mozilla firefox opera safari'.split():
        # Note: `macosx` fails on macOS 10.12.5 due to <http://bugs.python.org/issue30392>.
        try:
            b = webbrowser.get(name)
            if b.open(url):
                return True
        except Exception:
            pass
    return False



from .func_cache_utils import shelve_cache
@shelve_cache
def cached_get(url):
    import requests
    # Do we need to encode this response somehow?
    # Maybe as `(resp.status, resp.text)`?
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:62.0) Gecko/20100101 Firefox/62.0',
               'Accept-Language':'en-US,en;q=0.5',
    }
    return requests.get(url, headers=headers)
