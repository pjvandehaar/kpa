#!/usr/bin/env python3

## TODO: Move system_prompt to an option.

import argparse
import functools
import datetime, json
import os
from typing import Any, Optional
import requests
from pathlib import Path
from kpa.func_cache_utils import shelve_cache


request_logging_dir = Path('/tmp/kpa_llm_requests/')

class ApiOverloadedException(Exception):
    def __init__(self, message:str, wait_seconds:int|None=None):
        self.message = message
        self.wait_seconds = wait_seconds



def run_llm_command(argv:list[str]) -> None:

    if not argv or {'-h', '--help'}.intersection(argv):
        print("Usage:")
        print("  kpa llm -m gpt-4.1 'What is 7*8?'")
        print("  kpa llm -m gpt-4.1 prompt.txt")
        print("  kpa llm -m gpt-4.1 --instructions instructions.txt prompt.txt")
        print("  kpa llm --log")
        print("\nList of models:")
        for model_name in get_models_config().keys(): print(f"  {model_name}")
        return

    if argv[0] == '--log':  ## special case
        log_paths = sorted(request_logging_dir.glob('*.json'), key=lambda p: p.stat().st_mtime)
        print('All log files:')
        for log_path in log_paths: print(' -', log_path.name)
        print('\nLast log file content:')
        print(log_paths[-1].read_text())
        return

    ## Parse and resolve args:
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-m', '--model', type=str, default=str(list(get_models_config().keys())[0]))
    arg_parser.add_argument('--temperature', type=float, help="Not supported on all models")
    arg_parser.add_argument('--instructions', help="system prompt")
    arg_parser.add_argument('--no-print-logs', action='store_false', dest='print_logs', default=True)
    arg_parser.add_argument('user_prompt')
    args = arg_parser.parse_args(argv)

    model_name = get_full_model_name(args.model)
    if args.instructions and Path(args.instructions).expanduser().exists():
        instructions_text = Path(args.instructions).read_text()
        print('=> reading instructions from file:', args.instructions, f' ({len(args.instructions):,} chars)')
        args.instructions = instructions_text
    if args.user_prompt and Path(args.user_prompt).expanduser().exists():
        user_prompt_text = Path(args.user_prompt).read_text()
        print('=> reading user prompt from file:', args.user_prompt, f' ({len(user_prompt_text):,} chars)')
        args.user_prompt = user_prompt_text

    ## Run LLM:
    output, resp_data = run_llm(model_name, args.user_prompt, instructions=args.instructions, temperature=args.temperature)
    if args.print_logs: print(Path(resp_data['log_path']).read_text()); print()
    else: print(f"=> logs: {resp_data['log_path']}")
    print(output)


@shelve_cache
def run_llm(model_name:str, user_prompt:str, instructions:Optional[str]=None, request_label:str='', temperature:Optional[float]=None) -> tuple[str, dict]:
    ## TOOD: Support json_schema response_format, and list which models actually enforce that.
    if not request_label: request_label = f'{model_name}-{get_datetime_str()}'

    assert len(user_prompt) < 1e6, (len(user_prompt), user_prompt[-100:])
    if instructions: assert len(instructions) < 20e3, (len(instructions), instructions[-100:])

    model_config = get_models_config()[model_name]

    if model_config['api_type'] == 'openai': pass
    elif model_config['api_type'] == 'claude': pass
    elif model_config['api_type'] == 'bedrock': raise NotImplementedError('bedrock not implemented')
    elif model_config['api_type'] == 'ollama': pass  # TODO: Check that ollama server is running
    elif model_config['api_type'] == '/chat/completions': pass
    else: raise Exception(f'unknown api type: {model_config["api_type"]}')

    headers = {"Content-Type": "application/json"} | replace_api_key_placeholders(model_config.get('extra_headers', {}))

    data: dict[str, Any] = {
        "model": model_name,
        "stream": False,
        "store": False,
    }
    if temperature is not None:
        data['temperature'] = temperature
    if model_config['api_type'] == 'openai':
        data['input'] = [
            {"role": "developer", "content": instructions},
            {"role": "user", "content": user_prompt},
        ]
        if not data['input'][0]['content']: del data['input'][0]
    elif model_config['api_type'] == '/chat/completions':
        data['messages'] = [
            {"role": "system", "content": instructions},
            {"role": "user", "content": user_prompt},
        ]
        if not data['messages'][0]['content']: del data['messages'][0]
    else:  # This covers the other api_types
        if instructions: data['system'] = [{"type": "text", "text": instructions}]
        data['messages'] = [{"role": "user", "content": user_prompt}]

        if model_config['api_type'] == 'claude':
            del data['store']  # Not allowed
            data['max_tokens'] = 64_000  # Max allowed

    log_path = str(request_logging_dir / f'{request_label}.json')
    write_log(log_path, {
        "request_url": model_config['url'],
        "request_headers": headers,
        "request_data": data,
    })
    print(f"=> Logged req to {log_path}")

    response = requests.post(model_config['url'], headers=headers, json=data)
    try:
        x = response.json()
        assert isinstance(x, dict), x
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
    print(f"=> Logged resp to {log_path}")

    # if 'x-ratelimit-reset-requests' in response.headers or 'x-ratelimit-reset-tokens' in response.headers:  # This only applies if we got 5XX status!
    #     ## I know this applies to openai, but might as well include for the others.
    #     ## TODO: Parse "6m3s" etc.
    #     raise ApiOverloadedException(x.get('error', {}).get('message','error'), wait_seconds=120)
    if 'retry-after' in response.headers:
        ## I know this applies to claude, but might as well include for the others.
        wait_seconds = int(response.headers['retry-after'])
        raise ApiOverloadedException(x.get('error', {}).get('message','error'), wait_seconds=wait_seconds+1)

    if model_config['api_type'] == 'openai':
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
            raise Exception(f'unknown error from Claude: {x["error"]["message"]}')
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




### Read llm_keys.json:
@functools.cache
def get_llm_keys_config() -> dict[str,Any]:
    ## TODO: Use a forgiving json loader that allows comments, trailing commas, etc
    return json.loads(Path('~/PROJECTS/creds/llm_keys.json').expanduser().read_text())

def get_models_config() -> dict[str,dict[str,Any]]:
    return get_llm_keys_config()['llms']

def get_api_keys() -> dict[str,str]:
    """Returns {"openai": "sk-...", "claude": "sk-...", ...}."""
    config = get_llm_keys_config()
    return {service: keys[0]['key'] for service, keys in config['api_keys'].items()}

def replace_api_key_placeholders(headers:dict[str,str]) -> dict[str,str]:
    api_keys = get_api_keys()
    for header_name in list(headers.keys()):
        if isinstance(headers[header_name], str) and '$api_key_' in headers[header_name]:
            for service_name, api_key in api_keys.items():
                headers[header_name] = headers[header_name].replace(f'$api_key_{service_name}', api_key)
    return headers

def get_full_model_name(model_name_prefix:str) -> str:
    """Let user write `gem` to get `gemini-2.0-flash` (if that's the only model that starts with `gem`)"""
    models_config = get_models_config()
    if model_name_prefix in models_config: return model_name_prefix
    matching_models = [model_name for model_name in models_config.keys() if model_name.startswith(model_name_prefix)]
    if len(matching_models) == 1: return matching_models[0]
    elif len(matching_models) == 0: raise Exception(f'Model name prefix doesnt match any models: {model_name_prefix}')
    else: raise Exception(f'Model name prefix matches multiple models: {model_name_prefix}, matching models: {matching_models}')


### Utils:
def get_datetime_str() -> str:
    return datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

def write_log(log_path:str, data:dict[str, Any]) -> None:
    Path(log_path).parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, 'w') as f: json.dump(data, f, indent=2)
