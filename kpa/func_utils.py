
import boltons.funcutils

def assign(func):
    return func()
def assign_list(func):
    return list(func())

def only_once(func):
    already_ran = [False] # TODO: use `nonlocal` or `global` or whatever to avoid `[0]`
    @boltons.funcutils.wraps(func)
    def f(*args, **kwargs):
        if not already_ran[0]:
            already_ran[0] = True
            return func(*args, **kwargs)
    return f

def list_from_iter(func):
    @boltons.funcutils.wraps(func)
    def f(*args, **kwargs):
        return list(func(*args, **kwargs))
    return f
