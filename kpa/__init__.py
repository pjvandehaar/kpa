
def _f():
    import sys
    if sys.version_info < (3, 4):
        print("Requires Python 3.4+")
        sys.exit(1)

    import math
    try: math.inf
    except AttributeError: math.inf = float('inf')
_f()
del _f
