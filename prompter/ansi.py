import sys
from prompter import _ansi

ansi = _ansi.AnsiConfig()
ansi.__doc__ = __doc__
sys.modules[__name__] = ansi
