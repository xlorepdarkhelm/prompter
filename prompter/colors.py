import sys
from prompter import _colors

colors = _colors.ColorConfig()
colors.__doc__ = __doc__
sys.modules[__name__] = colors
