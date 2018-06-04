
import sys
import math

if sys.version_info < (3, 4):
    print("Requires Python 3.4+")
    sys.exit(1)


try: math.inf
except AttributeError: math.inf = float('inf')
