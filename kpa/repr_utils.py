
def repr_size(n:int) -> str:
    if n < 0: return f'-{repr_bytes(-n)}'
    if n > 1e11: return f'{n/1e12:.1f}TB'
    if n > 1e8: return f'{n/1e9:.1f}GB'
    if n > 1e5: return f'{n/1e6:.1f}MB'
    if n > 1e2: return f'{n/1e3:.1f}KB'
    return f'{n} bytes'
