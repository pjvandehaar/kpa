#!/usr/bin/env python3

import datetime, json
import os
from typing import Any
import requests
from pathlib import Path
from kpa.func_cache_utils import shelve_cache


request_logging_dir = Path('/tmp/kpa_llm_requests/')

class ApiOverloadedException(Exception):
    def __init__(self, message:str, wait_seconds:int|None=None):
        self.message = message
        self.wait_seconds = wait_seconds



def run_llm_command(args:list[str]) -> None:
    if args == ['--log']:
        log_paths = sorted(request_logging_dir.glob('*.json'), key=lambda p: p.stat().st_mtime)
        print('All log files:')
        for log_path in log_paths: print(' -', log_path.name)
        print('\nLast log file content:')
        print(log_paths[-1].read_text())
        return
    normal_args = [arg for arg in args if not arg.startswith('--')]
    if not normal_args or {'-h', '--help'}.intersection(normal_args):
        print(f"Usage: kpa llm <user_prompt>")
        print(f"Usage: kpa llm <model_name> <user_prompt>")
        print(f"Usage: kpa llm <model_name> <system_prompt> <user_prompt>")
        print("Usage: kpa llm --last-log")
        print("\nList of models:")
        for model_name in get_models_config().keys(): print(f"  {model_name}")
        return
    print_logs = '--no-print-logs' not in args
    args = [arg for arg in args if not arg.startswith('--')]

    models_config = get_models_config()
    model_name = str(list(models_config.keys())[0])
    system_prompt = ''
    user_prompt = ''
    if len(args) == 1: user_prompt = args[0]
    elif len(args) == 2: model_name, user_prompt = args
    elif len(args) == 3: model_name, system_prompt, user_prompt = args
    else: raise Exception(f'unknown args: {args}')
    model_name = get_full_model_name(model_name)
    if Path(system_prompt).expanduser().exists():
        system_prompt = Path(system_prompt).read_text()
        print('=> reading system prompt from file:', system_prompt, f' ({len(system_prompt):,} chars)')
    if Path(user_prompt).expanduser().exists():
        user_prompt = Path(user_prompt).read_text()
        print('=> reading user prompt from file:', user_prompt, f' ({len(user_prompt):,} chars)')
    try: model_config = models_config[model_name]
    except KeyError: raise Exception(f'unknown model {model_name}, available models: {list(models_config.keys())}')
    output, resp_data = run_llm(model_name, system_prompt, user_prompt)
    if print_logs: print(Path(resp_data['log_path']).read_text()); print()
    else: print(f"=> logs: {resp_data['log_path']}")
    print(output)


@shelve_cache
def run_llm(model_name:str, system_prompt:str, user_prompt:str, request_label:str='') -> tuple[str, dict]:
    ## TOOD: Support json_schema response_format, and list which models actually enforce that.
    if not request_label: request_label = f'{model_name}-{get_datetime_str()}'

    assert len(user_prompt) < 1e6, (len(user_prompt), user_prompt[-100:])
    assert len(system_prompt) < 10e3, (len(system_prompt), system_prompt[-100:])

    model_config = get_models_config()[model_name]

    if model_config['api_type'] == 'bedrock': raise NotImplementedError('bedrock not implemented')
    elif model_config['api_type'] == 'ollama': pass  # TODO: Check that ollama server is running
    elif model_config['api_type'] == 'openai': pass
    elif model_config['api_type'] == 'claude': pass
    elif model_config['api_type'] == '/chat/completions': pass
    else: raise Exception(f'unknown api type: {model_config["api_type"]}')

    headers = {"Content-Type": "application/json"} | model_config.get('extra_headers', {})
    if model_config['api_type'] == 'openai':
        data: dict[str, Any] = {
            "model": model_name,
            "input": [
                {"role": "developer", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "store": False,
        }
        if not data['input'][0]['content']: del data['input'][0]
    else:
        data: dict[str, Any] = {
            "model": model_name,
            "max_tokens": 8192,
            "system": [{"type": "text", "text": system_prompt}],
            "messages": [{"role": "user", "content": user_prompt}],
            "stream": False,
        }
        if not data['system'][0]['text']: del data['system']
    log_path = str(request_logging_dir / f'{request_label}.json')
    write_log(log_path, {
        "request_url": model_config['url'],
        "request_headers": headers,
        "request_data": data,
    })
    response = requests.post(model_config['url'], headers=headers, json=data)
    try:
        x = response.json()
    except Exception as e:
        write_log(log_path, {
            "request_url": model_config['url'],
            "request_headers": headers,
            "request_data": data,
            "response_status_code": response.status_code,
            "response_headers": dict(response.headers),
            "response_text": response.text,
            "error": str(e),
        })
        raise e
    write_log(log_path, {
        "request_url": model_config['url'],
        "request_headers": headers,
        "request_data": data,
        "response_status_code": response.status_code,
        "response_headers": dict(response.headers),
        "response_data": x,
    })


    if model_config['api_type'] == 'openai':
        if 'x-ratelimit-reset-requests' in response.headers or 'x-ratelimit-reset-tokens' in response.headers:
            ## TODO: Parse "6m3s" etc.
            raise ApiOverloadedException(x.get('error', {}).get('message','error'), wait_seconds=120)
        assert x.get('status') == 'completed' and x.get('error') is None, x
        actual_output = [msg for msg in x['output'] if msg['type'] == 'message']
        assert len(actual_output) == 1, dict(x=x, actual_output=actual_output)
        assert len(actual_output[0]['content']) == 1, dict(x=x, actual_output=actual_output)
        content0 = actual_output[0]['content'][0]
        assert content0['type'] == 'output_text', content0
        assert len(content0['annotations']) == 0, content0
        content0text = content0['text']
        del x['output']
        return (content0text, x | {'log_path': log_path})
    elif model_config['api_type'] == 'claude':
        if x['type'] == 'message':
            assert len(x['content']) == 1, x
            assert x['content'][0]['type'] == 'text', x
            assert sorted(x['content'][0]) == ['text', 'type'], x['content'][0]
            content0text = x['content'][0]['text']
            del x['content']
            return (content0text, x | {'log_path': log_path})
        elif x['type'] == 'error':
            if 'retry-after' in response.headers:
                wait_seconds = int(response.headers['retry-after'])
                raise ApiOverloadedException(x.get('error', {}).get('message','error'), wait_seconds=wait_seconds+1)
            else:
                raise Exception(f'unknown error: {x["error"]["message"]}')
        else:
            raise Exception(f'unknown response type: {x["type"]}')
    elif model_config['api_type'] == 'ollama':
        assert x['message']['role'] == 'assistant', x
        content = x['message']['content']
        assert isinstance(content, str) and content, content
        del x['message']
        return (content, x | {'log_path': log_path})
    elif model_config['api_type'] == '/chat/completions':
        assert len(x['choices']) == 1, x
        assert x['choices'][0]['message']['content'], x
        content = x['choices'][0]['message']['content']
        del x['choices']
        return (content, x | {'log_path': log_path})
    else:
        raise Exception(f'unknown api type: {model_config["api_type"]}')

def write_log(log_path:str, data:dict[str, Any]) -> None:
    Path(log_path).parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, 'w') as f: json.dump(data, f, indent=2)

def get_models_config() -> dict[str,str]:
    ## TODO: Use a forgiving json loader that allows comments, trailing commas, etc
    return json.loads(Path('~/PROJECTS/creds/llm_keys.json').expanduser().read_text())['llms']

def get_full_model_name(model_name_prefix:str) -> str:
    models_config = get_models_config()
    if model_name_prefix in models_config: return model_name_prefix
    matching_models = [model_name for model_name in models_config.keys() if model_name.startswith(model_name_prefix)]
    if len(matching_models) == 1: return matching_models[0]
    elif len(matching_models) == 0: raise Exception(f'Model name prefix doesnt match any models: {model_name_prefix}')
    else: raise Exception(f'Model name prefix matches multiple models: {model_name_prefix}, matching models: {matching_models}')


def get_datetime_str() -> str:
    return datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

