import sys
from prompter import _config

config = _config.MainConfig()
config.__doc__ = __doc__
sys.modules[__name__] = config
