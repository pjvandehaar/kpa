
import boltons.funcutils

def assign(func): return func()
def assign_list(func): return list(func()) # TODO: prefer `@assign @list_from_iter`, which also allows cacheing
def assign_dict(func): return dict(func())

def only_once(func):
    already_ran = [False] # TODO: use `nonlocal` or `global` or whatever to avoid `[0]`
    @boltons.funcutils.wraps(func)
    def f(*args, **kwargs):
        if not already_ran[0]:
            already_ran[0] = True
            return func(*args, **kwargs)
    return f

# def list_from_iter(func):
#     @boltons.funcutils.wraps(func)
#     def f(*args, **kwargs):
#         return list(func(*args, **kwargs))
#     return f

# def dict_from_iter(func):
#     @boltons.funcutils.wraps(func)
#     def f(*args, **kwargs):
#         return dict(func(*args, **kwargs))
#     return f

def apply_to_result(*result_wrapper_funcs):
    def wrap(func):
        @boltons.funcutils.wraps(func)
        def f(*args, **kwargs):
            result = func(*args, **kwargs)
            for result_wrapper_func in result_wrapper_funcs:
                result = result_wrapper_func(result)
            return result
        return f
    return wrap

list_from_iter = apply_to_result(list)
dict_from_iter = apply_to_result(dict)
