#!/usr/bin/env python3

import getpass
import os
import pwd
import socket

import psutil

from prompter import ansi
from prompter import colors
from prompter import config

USERDATA = pwd.getpwnam(getpass.getuser())
XTERM = 'TERM' in os.environ and os.environ['TERM'].casefold() == 'xterm'
HOSTNAME = socket.gethostname()
SUPER = USERDATA.pw_name in config.settings.user.super

USER = r'\u'
AT = '@'
HOST = r'\h'
COLON = ':'
PROMPT_SYMBOL = r'\$'
MEM_SEP = '/'
MEM_UNITS = 'MB'
SWAP_SEP = '/'
SWAP_UNITS = 'MB'
MEM_SYS_SEP = '\t'
SYS_SEP = ' '
PROCS_SEP = '/'
DIRNAME = ''.join([
    r'$(',
    '; '.join([
        r'EC=$?',
        r'DIRNAME=${PWD%/*}',
        r'if [[ $DIRNAME != "/" && $PWD != $HOME ]]',
        r'then echo ${DIRNAME/$HOME/"~"}',
        r'else echo ""',
        r'fi',
        r'exit $EC',
    ]),
    r')'
])
BASENAME = ''.join([
    r'$(',
    '; '.join([
        r'EC=$?',
        r'if [[ $PWD == $HOME || $PWD == "/" ]]',
        r'then echo "\W"',
        r'else echo "/\W"',
        r'fi',
        r'exit $EC',
    ]),
    r')'
])
TEST_FORMAT = ''.join([
    '$(',
    '; '.join([
        r'EC=$?',
        r'if [[ $EC -eq 0 ]]',
        'then echo "{color_good}"',
        'else echo "{color_bad}"',
        r'fi',
        r'exit $EC',
    ]),
    ')',
])

MEM_FORMAT = ''.join([
    '$(',
    '; '.join([
        r'EC=$?',
        '''MEM_FREE=$(free -k | grep '^Mem:' | awk '{print_line}')''',
        '{color_range}',
        r'exit $EC',
    ]),
    ')',
])
MEM_FREE = ''.join([
    '$(',
    '; '.join([
        r'EC=$?',
        '''echo "$(free -m | grep '^Mem:' | awk '{print $4}')"''',
        r'exit $EC',
    ]),
    ')',
])
MEM_TOTAL = ''.join([
    '$(',
    '; '.join([
        r'EC=$?',
        '''echo "$(free -m | grep '^Mem:' | awk '{print $2}')"''',
        r'exit $EC',
    ]),
    ')',
])

SWAP_FORMAT = ''.join([
    '$(',
    '; '.join([
        r'EC=$?',
        '''SWAP_FREE=$(free -k | grep '^Swap:' | awk '{print_line}')''',
        '{color_range}',
        r'exit $EC',
    ]),
    ')',
])
SWAP_FREE = ''.join([
    '$(',
    '; '.join([
        r'EC=$?',
        '''echo "$(free -m | grep '^Swap:' | awk '{print $4}')"''',
        r'exit $EC',
    ]),
    ')',
])
SWAP_TOTAL = ''.join([
    '$(',
    '; '.join([
        r'EC=$?',
        '''echo "$(free -m | grep '^Swap:' | awk '{print $2}')"''',
        r'exit $EC',
    ]),
    ')',
])

LOAD_1M_FORMAT = ''.join([
    '$(',
    '; '.join([
        r'EC=$?',
        ''.join([
            'LOADAVG_1=$(',
            ' | '.join(['cat /proc/loadavg', "cut -d ' ' -f 1"]),
            ')',
        ]),
        '{color_range}',
        r'exit $EC',
    ]),
    ')',
])
LOAD_1M = ''.join([
    '$(',
    '; '.join([
        r'EC=$?',
        ''.join([
            'echo "$(',
            ' | '.join(['cat /proc/loadavg', "cut -d ' ' -f 1"]),
            ')"',
        ]),
        r'exit $EC',
    ]),
    ')',
])
LOAD_5M_FORMAT = ''.join([
    '$(',
    '; '.join([
        r'EC=$?',
        ''.join([
            'LOADAVG_5=$(',
            ' | '.join(['cat /proc/loadavg', "cut -d ' ' -f 2"]),
            ')',
        ]),
        '{color_range}',
        r'exit $EC',
    ]),
    ')',
])
LOAD_5M = ''.join([
    '$(',
    '; '.join([
        r'EC=$?',
        ''.join([
            'echo "$(',
            ' | '.join(['cat /proc/loadavg', "cut -d ' ' -f 2"]),
            ')"',
        ]),
        r'exit $EC',
    ]),
    ')',
])
LOAD_15M_FORMAT = ''.join([
    '$(',
    '; '.join([
        r'EC=$?',
        ''.join([
            'LOADAVG_15=$(',
            ' | '.join(['cat /proc/loadavg', "cut -d ' ' -f 3"]),
            ')',
        ]),
        '{color_range}',
        r'exit $EC',
    ]),
    ')',
])
LOAD_15M = ''.join([
    '$(',
    '; '.join([
        r'EC=$?',
        ''.join([
            'echo "$(',
            ' | '.join(['cat /proc/loadavg', "cut -d ' ' -f 3"]),
            ')"',
        ]),
        r'exit $EC',
    ]),
    ')',
])
CUR_PROCS = ''.join([
    '$(',
    '; '.join([
        r'EC=$?',
        ''.join([
            'echo "$(',
            ' | '.join(['cat /proc/loadavg',
                "cut -d ' ' -f 4", "cut -d '/' -f 1"]),
            ')"',
        ]),
        r'exit $EC',
    ]),
    ')',
])
TTL_PROCS = ''.join([
    '$(',
    '; '.join([
        r'EC=$?',
        ''.join([
            'echo "$(',
            ' | '.join(['cat /proc/loadavg',
                "cut -d ' ' -f 4", "cut -d '/' -f 2"]),
            ')"',
        ]),
        r'exit $EC',
    ]),
    ')',
])
LAST_PID = ''.join([
    '$(',
    '; '.join([
        r'EC=$?',
        ''.join([
            'echo "$(',
            ' | '.join(['cat /proc/loadavg', "cut -d ' ' -f 5"]),
            ')"',
        ]),
        r'exit $EC',
    ]),
    ')',
])


def get_fore_color(color):
    if XTERM:
        seq = ansi.seq.ColorText
    else:
        seq = ansi.seq.AnsiColorText

    return seq(color)


def get_back_color(color):
    if XTERM:
        seq = ansi.seq.ColorBack
    else:
        seq = ansi.seq.AnsiColorBack

    return seq(color)


def get_color(fore=None, back=None):
    items = []

    if fore is not None:
        items.append(get_fore_color(fore))

    if back is not None:
        items.append(get_back_color(back))

    if items:
        return sum(items)
    else:
        return ''


def get_color_from_config(value):
    if isinstance(value, config.Base):  # Is a defined color.
        if 'cube6' in value:
            return colors.from_cube6(**value.cube6)
        elif 'cube5' in value:
            return colors.from_cube5(**value.cube5)
        elif 'cube6_xterm' in value:
            return colors.from_cube6_xterm(**value.cube6_xterm)
        elif 'ansi' in value:
            return colors.from_ansi(**value.ansi)
        elif 'xterm' in value:
            return colors.from_xterm(value.xterm)
        elif 'rgb' in value:
            return colors.from_rgb(**value.rgb)
        elif 'hsv' in value:
            return colors.from_hsv(**value.hsv)
        elif 'hsl' in value:
            return colors.from_hsl(**value.hsl)
        elif 'grayscale' in value:
            return colors.from_grayscale(value.grayscale)
        else:
            return colors.Black

    else:  # Specifies a named color
        return colors[value]


def gen_pct_range_gradient(range):
    ttl_keys = sorted(list(range.keys()))
    key_range = zip(ttl_keys[:-1], ttl_keys[1:])

    last_high = 0

    used = set()

    first = True

    for low, high in key_range:
        low_color = range[low]
        high_color = range[high]
        if not isinstance(range[low], int) or not isinstance(range[high], int):
            low_color = get_color_from_config(low_color)
            high_color = get_color_from_config(high_color)

            color_gradient = list(
                low_color.cube6_xterm.gen_hsv_gradient(high_color)
            )

        else:
            color_gradient = list(
                colors.from_grayscale(low_color).xterm.
                gen_grayscale_gradient(colors.from_grayscale(high_color))
            )

        if not first:
            color_gradient = color_gradient[1:]

        last_pct = 0

        for ndx, color in enumerate(color_gradient):
            pct = last_high + (
                (ndx + (0 if first else 1)) * (
                    (high - low) / (len(color_gradient) - (1 if first else 0))
                ) / 100
            )

            if hasattr(color, 'rgb'):
                color = color.rgb

            if pct not in used:
                last_pct = pct
                used.add(pct)

                yield pct, color

        last_high = last_pct

        first = False


def gen_mem_range_gradient():
    yield from (
        (
            int((psutil.virtual_memory().total / 1024) * pct + 0.5),
            color
        )
        for pct, color in gen_pct_range_gradient(config.settings.memory.range)
    )


def get_mem_free_color_range():
    return '; '.join([
        '; el'.join(
            '; '.join([
                'if [[ $MEM_FREE -ge {threshold} ]]',
                'then echo "{color}"'
            ]).format(
                threshold=threshold,
                color=get_fore_color(color)
            )
            for threshold, color in reversed(list(gen_mem_range_gradient()))
        ),
        'fi'
    ])


def gen_swap_range_gradient():
    yield from (
        (
            int((psutil.swap_memory().total / 1024) * pct + 0.5),
            color
        )
        for pct, color in gen_pct_range_gradient(config.settings.swap.range)
    )


def get_swap_free_color_range():
    return '; '.join([
        '; el'.join(
            '; '.join([
                'if [[ $SWAP_FREE -ge {threshold} ]]',
                'then echo "{color}"'
            ]).format(
                threshold=threshold,
                color=get_fore_color(color)
            )
            for threshold, color in reversed(list(gen_swap_range_gradient()))
        ),
        'fi'
    ])


def gen_load_range_gradient(name):
    yield from (
        (1.0 - pct, color)
        for pct, color in gen_pct_range_gradient(
            config.settings.sys.load[name].back
        )
    )


def get_load_avg_color_range(mins):
    name = 'avg_{mins}m'.format(mins=mins)
    return '; '.join([
        '; el'.join(
            '; '.join([
                ' '.join([
                    'if',
                    '[[',
                    ''.join([
                        '$(',
                        ' | '.join(['echo "$LOADAVG_{mins}>={threshold}"',
                            'bc -l']),
                        ')'
                    ]),
                    '==',
                    '1',
                    ']]'
                ]),
                'then echo "{back_color}"'
            ]).format(
                mins=mins,
                threshold=threshold,
                back_color=get_back_color(color)
            )
            for threshold, color in gen_load_range_gradient(name)
        ),
        'fi'
    ])


class Prompt(config.Base):
    def __init__(self):
        self.bad_names |= {
            'color_wrap',
            'non_printing',
            'wrap',
        }

        self.register_attr(
            'usercolor',
            lambda: (
                get_color_from_config(
                    config.settings.user.super[USERDATA.pw_name]
                )
                if SUPER
                else get_color_from_config(
                    config.settings.user.normal[USERDATA.pw_name]
                )
            ),
            'The color to use for the current user'
        )

        self.register_attr(
            'at_color',
            lambda: get_color_from_config(config.settings.at_symbol),
            'The color to use for the at symbol'
        )

        self.register_attr(
            'hostcolor',
            lambda: (
                get_color_from_config(
                    config.settings.server[HOSTNAME].super
                )
                if SUPER
                else get_color_from_config(
                    config.settings.server[HOSTNAME].normal
                )
            ),
            'The color to use for the hostname'
        )

        self.register_attr(
            'colon_color',
            lambda: get_color_from_config(config.settings.colon),
            'The color to use for the colon symbol'
        )

        self.register_attr(
            'dirname_color',
            lambda: get_color_from_config(config.settings.dirname),
            'The color to use for the current dirname'
        )

        self.register_attr(
            'basename_color',
            lambda: get_color_from_config(config.settings.basename),
            'The color to use for the current basename'
        )

        self.register_attr(
            'good_fore_color',
            lambda: get_color_from_config(config.settings.test.good.fore),
            'The text color to use when the previous command succeeded.'
        )

        self.register_attr(
            'good_back_color',
            lambda: get_color_from_config(config.settings.test.good.back),
            'The back color to use when the previous command succeeded.'
        )

        self.register_attr(
            'bad_fore_color',
            lambda: get_color_from_config(config.settings.test.bad.fore),
            'The text color to use when the previous command failed.'
        )

        self.register_attr(
            'bad_back_color',
            lambda: get_color_from_config(config.settings.test.bad.back),
            'The back color to use when the previous command failed.'
        )

        self.register_attr(
            'test_good',
            lambda: get_color(self.good_fore_color, self.good_back_color),
            ' '.join([
                'The complete color configuration for when',
                'the previous command succeeded'
            ])
        )

        self.register_attr(
            'test_bad',
            lambda: get_color(self.bad_fore_color, self.bad_back_color),
            ' '.join([
                'The complete color configuration for when',
                'the previous command failed'
            ])
        )

        self.register_attr(
            'test_color',
            lambda: TEST_FORMAT.format(
                color_good=self.test_good,
                color_bad=self.test_bad
            ),
            'Returns the complete color setting for previous command test'
        )

        self.register_attr(
            'test',
            lambda: ''.join([
                self.wrap(
                    PROMPT_SYMBOL,
                    self.test_color
                ),
                ' '
            ])
        )

        self.register_attr(
            'reset_colors',
            lambda: (
                ansi.seq.ResetColorText()
                + ansi.seq.ResetColorBack()
                + ansi.seq.Reset()
            )
        )

        self.register_attr(
            'user_host',
            lambda: (
                self.color_wrap(
                    ''.join([USER, AT, HOST]),
                    self.usercolor,
                    self.hostcolor
                )
                if SUPER
                else ''.join([
                    self.color_wrap(USER, self.usercolor),
                    self.color_wrap(AT, self.at_color),
                    self.color_wrap(HOST, self.hostcolor),
                ])
            ),
            'Gets the username@hostname component for the prompt.'
        )

        self.register_attr(
            'colon',
            lambda: self.wrap(
                COLON,
                ansi.seq.Bold() + get_color(self.colon_color)
            ),
            'Gets the colon component for the prompt.'
        )

        self.register_attr(
            'full_path',
            lambda: ''.join([
                self.color_wrap(DIRNAME, self.dirname_color),
                self.wrap(
                    BASENAME,
                    ansi.seq.Bold() + get_color(self.basename_color)
                ),
            ])
        )

        self.register_attr(
            'user_host_path',
            lambda: ''.join([
                self.user_host,
                self.colon,
                self.full_path,
            ]),
            'Gets the username@hostname:/path component for the prompt.'
        )

        self.register_attr(
            'mem_free',
            lambda: self.wrap(
                MEM_FREE,
                MEM_FORMAT.format(
                    print_line='{print $4}',
                    color_range=get_mem_free_color_range()
                )
            ),
            'Gets the memory free component for the prompt.'
        )

        self.register_attr(
            'mem_total',
            lambda: self.color_wrap(
                MEM_TOTAL,
                get_color_from_config(config.settings.memory.total)
            ),
            'Gets the memory total component for the prompt.'
        )

        self.register_attr(
            'mem_sep',
            lambda: self.color_wrap(
                MEM_SEP,
                get_color_from_config(config.settings.memory.sep)
            ),
            'Gets the separator for memory components for the prompt.'
        )

        self.register_attr(
            'mem_units',
            lambda: self.color_wrap(
                MEM_UNITS,
                get_color_from_config(config.settings.memory.units)
            ),
            'Gets the units for memory components for the prompt.'
        )

        self.register_attr(
            'memory',
            lambda: ''.join([
                self.mem_free,
                self.mem_sep,
                self.mem_total,
                self.mem_units,
            ]),
            'Gets the memory free/total component for the prompt.'
        )

        self.register_attr(
            'swap_free',
            lambda: self.wrap(
                SWAP_FREE,
                SWAP_FORMAT.format(
                    print_line='{print $4}',
                    color_range=get_swap_free_color_range()
                )
            ),
            'Gets the swap free component for the prompt.'
        )

        self.register_attr(
            'swap_total',
            lambda: self.color_wrap(
                SWAP_TOTAL,
                get_color_from_config(config.settings.swap.total)
            ),
            'Gets the swap total component for the prompt.'
        )

        self.register_attr(
            'swap_sep',
            lambda: self.color_wrap(
                SWAP_SEP,
                get_color_from_config(config.settings.swap.sep)
            ),
            'Gets the separator for swap components for the prompt.'
        )

        self.register_attr(
            'swap_units',
            lambda: self.color_wrap(
                SWAP_UNITS,
                get_color_from_config(config.settings.swap.units)
            ),
            'Gets the units for swap components for the prompt.'
        )

        self.register_attr(
            'swap',
            lambda: ''.join([
                self.swap_free,
                self.swap_sep,
                self.swap_total,
                self.swap_units,
            ]),
            'Gets the swap free/total component for the prompt.'
        )

        self.register_attr(
            'mem_swap',
            lambda: ' '.join([
                self.memory,
                self.swap,
            ]),
            'Gets the combined memory & swap components for the prompt.'
        )

        self.register_attr(
            'load1',
            lambda: ' '.join([
                self.wrap(
                    ' ',
                    LOAD_1M_FORMAT.format(
                        color_range=get_load_avg_color_range(1)
                    )
                ),
                self.color_wrap(
                    LOAD_1M,
                    get_color_from_config(
                        config.settings.sys.load['avg_1m'].fore
                    )
                ),
            ]),
            'Gets the Avg Load 1m component for the prompt.'
        )

        self.register_attr(
            'load5',
            lambda: ' '.join([
                self.wrap(
                    ' ',
                    LOAD_5M_FORMAT.format(
                        color_range=get_load_avg_color_range(5)
                    )
                ),
                self.color_wrap(
                    LOAD_5M,
                    get_color_from_config(
                        config.settings.sys.load['avg_5m'].fore
                    )
                ),
            ]),
            'Gets the Avg Load 5m component for the prompt.'
        )

        self.register_attr(
            'load15',
            lambda: ' '.join([
                self.wrap(
                    ' ',
                    LOAD_15M_FORMAT.format(
                        color_range=get_load_avg_color_range(15)
                    )
                ),
                self.color_wrap(
                    LOAD_15M,
                    get_color_from_config(
                        config.settings.sys.load['avg_15m'].fore
                    )
                ),
            ]),
            'Gets the Avg Load 15m component for the prompt.'
        )

        self.register_attr(
            'load_avg',
            lambda: SYS_SEP.join([
                self.load1,
                self.load5,
                self.load15
            ]),
            'Gets the combined Avg Load component for the prompt.'
        )

        self.register_attr(
            'cur_procs',
            lambda: self.color_wrap(
                CUR_PROCS,
                get_color_from_config(config.settings.sys.procs.current)
            ),
            'Gets the current processes component for the prompt.'
        )

        self.register_attr(
            'ttl_procs',
            lambda: self.color_wrap(
                TTL_PROCS,
                get_color_from_config(config.settings.sys.procs.total)
            ),
            'Gets the total processes component for the prompt.'
        )

        self.register_attr(
            'sep_procs',
            lambda: self.color_wrap(
                PROCS_SEP,
                get_color_from_config(config.settings.sys.procs.sep)
            ),
            'Gets the separator for processes components for the prompt.'
        )

        self.register_attr(
            'procs',
            lambda: ''.join([
                self.cur_procs,
                self.sep_procs,
                self.ttl_procs
            ]),
            'Gets the combined processes component for the prompt.'
        )

        self.register_attr(
            'last_pid',
            lambda: self.color_wrap(
                LAST_PID,
                get_color_from_config(config.settings.sys.last_pid)
            ),
            'Gets the last PID component for the prompt.'
        )

        self.register_attr(
            'sys',
            lambda: SYS_SEP.join([
                self.load_avg,
                self.procs,
                self.last_pid,
            ]),
            'Gets the combined system information component for the prompt.'
        )

        self.register_attr(
            'mem_sys',
            lambda: MEM_SYS_SEP.join([
                self.mem_swap,
                self.sys
            ]),
            'Gets the memory & system information component for the prompt.'
        )

        self.register_attr(
            'prompt',
            lambda: '\n'.join([
                self.mem_sys,
                self.user_host_path,
                self.test
            ]).replace('\033', r'\e'),
            'Gets the complete prompt.'
        )

    def wrap(self, text, start, end=None):
        if end is None:
            end = self.reset_colors

        return ''.join([
            self.non_printing(start),
            text,
            self.non_printing(end)
        ])

    def color_wrap(self, text, fore=None, back=None):
        return self.wrap(text, get_color(fore=fore, back=back))

    @staticmethod
    def non_printing(sequence):
        return ''.join(['\\[', str(sequence), '\\]'])

    @classmethod
    def get_prompt(cls):
        prompt = cls()

        print(prompt.prompt)


if __name__ == '__main__':
    Prompt.get_prompt()
