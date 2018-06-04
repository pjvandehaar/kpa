
import shelve, json, os.path

def shelve_cache(func):
    def new_f(*args, **kwargs):
        key = json.dumps([args, kwargs])
        with shelve.open(f'.cache-{func.__name__}.shelve') as shelf:
            if key not in shelf: shelf[key] = func(*args, **kwargs)
            return shelf[key]
    return new_f


def cached_generator(record_maker=lambda x:x):
    '''
    caches a generator into jsonlines format.
    calls record_maker on each un-serialized line before yielding it.
    '''
    def decorator(func):
        cache_fpath = os.path.join(f'.cache-{func.__name__}.jsonlines')
        def newf():
            if not os.path.exists(cache_fpath):
                with open(cache_fpath+'.tmp', 'wt') as f:
                    for r in func():
                        f.write(json.dumps(r) + '\n')
                        yield r
                os.rename(cache_fpath+'.tmp', cache_fpath)
            else:
                with open(cache_fpath, 'rt') as f:
                    for line in f:
                        yield record_maker(json.loads(line))
        return newf
    return decorator
