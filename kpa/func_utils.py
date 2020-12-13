
import functools
from typing import List, Callable, Any, Iterable, TypeVar, Tuple, Dict

T = TypeVar('T')
T2 = TypeVar('T2')

def assign(func: Callable[..., T]) -> T: return func()
def assign_list(func): return list(func()) # TODO: prefer `@assign @list_from_iter`, which also allows cacheing
def assign_dict(func): return dict(func())

def only_once(func: Callable[..., T]) -> Callable[..., T]:
    already_ran = [False] # TODO: use `nonlocal` or `global` or whatever to avoid `[0]`
    @functools.wraps(func)
    def f(*args, **kwargs):
        if not already_ran[0]:
            already_ran[0] = True
            return func(*args, **kwargs)
    return f

def list_from_iter(func: Callable[..., Iterable[T]]) -> Callable[..., List[T]]:
    @functools.wraps(func)
    def f(*args, **kwargs):
        return list(func(*args, **kwargs))
    return f

def dict_from_iter(func: Callable[..., Iterable[Tuple[T, T2]]]) -> Callable[..., Dict[T, T2]]:
    @functools.wraps(func)
    def f(*args, **kwargs):
        return dict(func(*args, **kwargs))
    return f

# Too complex to typecheck
def apply_to_result(*result_wrapper_funcs):
    def wrap(func):
        @functools.wraps(func)
        def f(*args, **kwargs) -> Any:
            result = func(*args, **kwargs)
            for result_wrapper_func in result_wrapper_funcs:
                result = result_wrapper_func(result)
            return result
        return f
    return wrap
