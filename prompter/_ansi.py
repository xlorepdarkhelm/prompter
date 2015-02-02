#1/usr/bin/env python3

import collections
import enum
import functools

from prompter import config

ESC = '\033'


def raise_(e):
    raise e


class EraseCode(enum.IntEnum):
    End = 0
    Start = 1
    All = 2


class SequenceWrapper:
    def __init__(self, suffix):
        self.suffix = suffix

    def __call__(self, func):
        @functools.wraps(func)
        def sequence_wrapper(*args, **kwargs):
            return '{esc}[{package}{suffix}'.format(
                esc=ESC,
                package=func(*args, **kwargs),
                suffix=self.suffix
            )

        return sequence_wrapper


class AnsiList(collections.UserList):
    def __iadd__(self, other):
        if not other:
            pass

        elif isinstance(other, AnsiList):
            self.extend(other)

        elif isinstance(other, AnsiSequence):
            self.append(other)

        else:
            raise ValueError('Can only combine with AnsiList or AnsiSequence')

        return self

    def __add__(self, other):
        if not other:
            clone = self.copy()

        elif isinstance(other, (AnsiList, AnsiSequence)):
            clone = self.copy()
            clone += other

        else:
            raise ValueError('Can only combine with AnsiList or AnsiSequence')

        return clone

    def __radd__(self, other):
        if not other:
            ret = self

        elif isinstance(other, AnsiSequence):
            self.insert(0, other)
            ret = self

        elif isinstance(other, AnsiList):
            other.extend(self)
            ret = other

        else:
            raise ValueError('Can only combine with AnsiList or AnsiSequence')

        return ret

    def __repr__(self):
        return 'AnsiList({items!r})'.format(items=self.data)

    def __str__(self):
        last_code = None

        ret = ''
        for item in self:
            if last_code is None:
                ret = ''.join([
                    ret,
                    AnsiSequence.CSI,
                    ';'.join(str(piece) for piece in item.payload)
                ])

            elif last_code == item.code:
                ret = ''.join([
                    ret,
                    (
                        ''.join([
                            ';',
                            ';'.join(str(piece) for piece in item.payload)
                        ])
                        if item.payload
                        else ''
                    )
                ])

            elif last_code != item.code:
                ret = ''.join([
                    ret,
                    last_code,
                    AnsiSequence.CSI,
                    ';'.join(str(piece) for piece in item.payload)
                ])

            last_code = item.code

        return ''.join([ret, last_code if last_code is not None else ''])


class AnsiSequence:
    CSI = ''.join([ESC, '['])

    def __init__(self, *payload, code):
        self.__code = code
        self.__payload = tuple(payload)

    @property
    def code(self):
        return self.__code

    @property
    def payload(self):
        return self.__payload

    def __add__(self, other):
        if not other:
            ret = self

        elif isinstance(other, AnsiSequence):
            ret = AnsiList()
            ret.append(self)
            ret.append(other)

        elif isinstance(other, AnsiList):
            ret = other
            ret.insert(0, self)

        else:
            raise ValueError('Can only combine with AnsiList or AnsiSequence')

        return ret

    def __iadd__(self, other):
        if not other:
            ret = self

        elif isinstance(other, AnsiSequence):
            ret = AnsiList()
            ret.append(self)
            ret.append(other)

        elif isinstance(other, AnsiList):
            ret = other
            ret.insert(0, self)

        else:
            raise ValueError('Can only combine with AnsiList or AnsiSequence')

        return ret

    def __radd__(self, other):
        if not other:
            ret = self

        elif isinstance(other, AnsiSequence):
            ret = AnsiList()
            ret.append(other)
            ret.append(self)

        elif isinstance(other, AnsiList):
            ret = other
            ret.append(self)

        else:
            raise ValueError('Can only combine with AnsiList or AnsiSequence')

        return ret

    def __str__(self):
        return ''.join([
            AnsiSequence.CSI,
            ';'.join(str(item) for item in self.payload),
            self.code
        ])

    def __repr__(self):
        payload_params = (
            ''.join([
                ', '.join(repr(item) for item in self.payload)
            ])
            if self.payload
            else ''
        )

        code_param = 'code={code!r}'.format(code=self.code)

        params = ', '.join([
            piece
            for piece in (payload_params, code_param)
            if piece
        ])

        return ''.join([
            type(self).__name__,
            '(',
            params,
            ')',
        ])


class SequenceConfig(config.Base):
    def __init__(self):
        self.register_attr(
            'CursorUp',
            lambda: lambda lines=1: AnsiSequence(lines, code='A'),
            """
            Moves cursor up by *lines* lines (1 by default).

            :param lines: Number of lines to move the cursor up
            :type lines: integer
            """
        )

        self.register_attr(
            'CursorDown',
            lambda: lambda lines=1: AnsiSequence(lines, code='B'),
            """
            Moves cursor down by *lines* lines (1 by default).

            :param lines: Number of lines to move the cursor down
            :type lines: integer
            """
        )

        self.register_attr(
            'CursorRight',
            lambda: lambda rows=1: AnsiSequence(rows, code='C'),
            """
            Moves cursor right by *rows* rows (1 by default).

            :param rows: Number of rows to move the cursor right
            :type rows: integer
            """
        )

        self.register_attr(
            'CursorLeft',
            lambda: lambda rows=1: AnsiSequence(rows, code='D'),
            """
            Moves cursor left by *rows* rows (1 by default).

            :param rows: Number of rows to move the cursor left
            :type rows: integer
            """
        )

        self.register_attr(
            'CursorDownHome',
            lambda: lambda lines=1: AnsiSequence(lines, code='E'),
            """
            Moves cursor to beginning of the line *lines* (1 by default) lines
            down.

            :param lines: Number of lines to move the cursor down
            :type lines: integer
            """
        )

        self.register_attr(
            'CursorUpHome',
            lambda: lambda lines=1: AnsiSequence(lines, code='F'),
            """
            Moves cursor to beginning of the line *lines* (1 by default) lines
            up.

            :param lines: Number of lines to move the cursor up
            :type lines: integer
            """
        )

        self.register_attr(
            'ColSet',
            lambda: lambda col: AnsiSequence(col, code='G'),
            """
            Moves the cursor to column *col* (absolute, 1-based).

            :param col: The column to move the cursor to.
            :type col: integer
            """
        )

        self.register_attr(
            'PosSet',
            lambda: lambda row, col: AnsiSequence(row, col, code='H'),
            """
            Set cursor position. The values *row* and *col* are 1-based.

            :param row: The row to move the cursor to.
            :type row: integer
            :param col: The column to move the cursor to.
            :type col: integer
            """
        )

        self.register_attr(
            'EraseScreen',
            lambda: lambda ec=EraseCode.End: AnsiSequence(
                (
                    ec.value
                    if isinstance(ec, EraseCode)
                    else ec
                    if ec in range(3)
                    else raise_(
                        ValueError(
                            ' '.join([
                                'ec must be an EraseCode or integer in the',
                                'range 0-2, and not {ec!r}.'
                            ]).format(
                                ec=ec
                            )
                        )
                    )
                ),
                code='J'
            ),
            """
            Erase display.

            * When *ec* is :py:attr:`EraseCode.End` or missing: from cursor toi
                end of display.
            * When *ec* is :py:attr:`EraseCode.Start`: erase from start to
                cursor.
            * When *ec* is :py:attr:`EraseCode.All`: erase whole display and
                moves cursor to upper-left corner.

            :param ec: The code that determines how the display erasing will
                work.
            :type ec: :py:class:`EraseCode`
            """
        )

        self.register_attr(
            'EraseLine',
            lambda: lambda ec=EraseCode.End: AnsiSequence(
                (
                    ec.value
                    if isinstance(ec, EraseCode)
                    else ec
                    if ec in range(3)
                    else raise_(
                        ValueError(
                            ' '.join([
                                'ec must be an EraseCode or an integer in the',
                                'range 0-2, and not {ec!r}.'
                            ]).format(
                                ec=ec
                            )
                        )
                    )
                ),
                code='K'
            ),
            """
            Erase line.

            * When *ec* is :py:attr:`EraseCode.End` or missing: from cursor to
                end of line.
            * When *ec* is :py:attr:`EraseCode.Start`: erase from start of line
                to cursor.
            * When *ec* is :py:attr:`EraseCode.All`: erase whole line and moves
                cursor to first column.

            :param ec: The code that determines how the line erasing will work.
            :type ec: :py:class:`EraseCode`
            """
        )

        self.register_attr(
            'InsertLine',
            lambda: lambda n=1: AnsiSequence(n, code='L'),
            """
            Insert *n* (default 1) lines before current, scroll part of screen
            from current line to bottom.

            :param n: Number of lines to insert
            :type n: integer
            """
        )

        self.register_attr(
            'DeleteLine',
            lambda: lambda n=1: AnsiSequence(n, code='M'),
            """
            Delete *n* (default 1) lines including current.

            :param n: Number of lines to delete
            :type n: integer
            """
        )

        self.register_attr(
            'ScrollUp',
            lambda: lambda lines: AnsiSequence(lines, code='S'),
            """
            Scroll screen (whole buffer) up by *lines*. New lines are added at
            the bottom.

            :param lines: Number of lines to scroll the screen up by.
            :type lines: integer
            """
        )

        self.register_attr(
            'ScrollDown',
            lambda: lambda lines: AnsiSequence(lines, code='T'),
            """
            Scroll screen (whole buffer) down by *lines*. New lines are added
            at the top.

            :param lines: Number of lines to scroll the screen down by.
            :type lines: integer
            """
        )

        self.register_attr(
            'EraseChar',
            lambda: lambda n=1: AnsiSequence(n, code='X'),
            """
            Erase *n* (default 1) characters from cursor (fill with spaces and
            default attributes).

            :param n: Number of characters to delete
            :type n: integer
            """
        )

        self.register_attr(
            'ScrollSet',
            lambda: lambda a=None, b=None: (
                AnsiSequence(a, b, code='r')
                if a is not None and b is not None
                else AnsiSequence(code='r')
            ),
            """
            Set scrolling region from top=*a* to bottom=*b*. The values *a* and
            *b* are 1-based. *Omit values to reset region.*

            :param a: The top row position for the scrolling region (absolute
                value)
            :type a: integer
            :param b: The bottom row position for the scrolling region
                (absolute value)
            :type b: integer
            """
        )

        self.register_attr(
            'PosSave',
            lambda: lambda: AnsiSequence(code='s'),
            """
            Save vursor position (cannot be nested).
            """
        )

        self.register_attr(
            'PosRestore',
            lambda: lambda: AnsiSequence(code='u'),
            """
            Restore cursor position.
            """
        )

        self.register_attr(
            'GetGTC',
            lambda: lambda: AnsiSequence(code='>c'),
            """
            Report "ESC > 67 ; build ; 0 c"
            """
        )

        self.register_attr(
            'GetC',
            lambda: lambda: AnsiSequence(code='c'),
            """
            Report "ESC [ ? 1 ; 2 c"
            """
        )

        self.register_attr(
            'GetStatus',
            lambda: lambda: AnsiSequence(5, code='n'),
            """
            Report status as "CSI 0 n" (OK)
            """
        )

        self.register_attr(
            'GetPos',
            lambda: lambda: AnsiSequence(6, code='n'),
            """
            Report Cursor Position as "ESC [ row ; col R"
            """
        )

        self.register_attr(
            'GetTextArea',
            lambda: lambda: AnsiSequence(18, code='t'),
            """
            Report the size of the text area in characters as
            "ESC [ 8 ; height ; width t"
            """
        )

        self.register_attr(
            'GetScreen',
            lambda: lambda: AnsiSequence(19, code='t'),
            """
            Report the size of the screen in characters as
            "ESC [ 9 ; height ; width t"
            """
        )

        self.register_attr(
            'GetTitle',
            lambda: lambda: AnsiSequence(21, code='t'),
            """
            Report window's title as "ESC ] l title ESC \\"
            """
        )

        self.register_attr(
            'LineWrapOn',
            lambda: lambda col=80: AnsiSequence(7, col, code='h'),
            """
            Enable lines wrapping at column position. If *col* (1-based) is
            absent, wrap at column 80.

            :param col: The column to wrap lines at.
            :type col: integer
            """
        )

        self.register_attr(
            'LineWrapOff',
            lambda: lambda: AnsiSequence(7, code='l'),
            """
            Disables line wrapping. Lines wrap at the end of screen buffer.
            """
        )

        self.register_attr(
            'CursorShow',
            lambda: lambda: AnsiSequence(25, code='h'),
            """
            Show text cursor.
            """
        )

        self.register_attr(
            'CursorHide',
            lambda: lambda: AnsiSequence(25, code='l'),
            """
            Hide text cursor.
            """
        )

        self.register_attr(
            'SetTitle',
            ''.join([ESC, '\\']),
            lambda: lambda txt: AnsiSequence(
                ''.join([
                    '"',
                    txt.encode('string_escape').replace('"', '\\"'),
                    '"',
                ]),
                code=''.join([ESC, '\\'])
            ),
            """
            Set console window title to *txt*.

            :param txt: The text to change the console window's title to.
            :type txt: string
            """
        )

        self.register_attr(
            'Reset',
            lambda: lambda: AnsiSequence(0, code='m'),
            """
            Reset current attributes.
            """
        )

        self.register_attr(
            'Bold',
            lambda: lambda: AnsiSequence(1, code='m'),
            """
            Set Bright or Bold.
            """
        )

        self.register_attr(
            'UnBold',
            lambda: lambda: AnsiSequence(2, code='m'),
            """
            Unset Bright or Bold.

            .. warning::

                This is unreliable. It is better to use
                :py:attr:`Sequence.Reset`
            """
        )

        self.register_attr(
            'Italic',
            lambda: lambda: AnsiSequence(3, code='m'),
            """
            Set Italic or Inverse.
            """
        )

        self.register_attr(
            'Underline',
            lambda: lambda: AnsiSequence(4, code='m'),
            """
            Set Underline or Back.
            """
        )

        self.register_attr(
            'Blink',
            lambda: lambda: AnsiSequence(5, code='m'),
            """
            Set Blink or Underline.
            """
        )

        self.register_attr(
            'Inverse',
            lambda: lambda: AnsiSequence(7, code='m'),
            """
            Set Inverse.
            """
        )

        self.register_attr(
            'Invisible',
            lambda: lambda: AnsiSequence(8, code='m'),
            """
            Set Invisible.
            """
        )

        self.register_attr(
            'UnItalic',
            lambda: lambda: AnsiSequence(23, code='m'),
            """
            Unset Italic or Inverse.

            .. warning::

                This is unreliable. It is better to use
                :py:attr:`Sequence.Reset`
            """
        )

        self.register_attr(
            'UnUnderline',
            lambda: lambda: AnsiSequence(24, code='m'),
            """
            Unset Underline or Back.

            .. warning::

                This is unreliable. It is better to use
                :py:attr:`Sequence.Reset`
            """
        )

        self.register_attr(
            'UnBlink',
            lambda: lambda: AnsiSequence(25, code='m'),
            """
            Unset Blink or Underline.

            .. warning::

                This is unreliable. It is better to use
                :py:attr:`Sequence.Reset`
            """
        )

        self.register_attr(
            'UnInverse',
            lambda: lambda: AnsiSequence(27, code='m'),
            """
            Unset Inverse.

            .. warning::

                This is unreliable. It is better to use
                :py:attr:`Sequence.Reset`
            """
        )

        self.register_attr(
            'UnInvisible',
            lambda: lambda: AnsiSequence(28, code='m'),
            """
            Unset Invisible.

            .. warning::

                This is unreliable. It is better to use
                :py:attr:`Sequence.Reset`
            """
        )

        self.register_attr(
            'AnsiColorText',
            lambda: lambda color: AnsiSequence(
                *(
                    [1 if color.ansi[1] else 2, 30 + color.ansi[0]]
                    if hasattr(color, 'ansi')
                    else [1 if color.ansi[1] else 2, 30 + color.rgb.ansi[0]]
                    if hasattr(color, 'rgb') and hasattr(color.rgb, 'ansi')
                    else [30 + color]
                    if color in range(8)
                    else raise_(
                        ValueError(
                            ' '.join([
                                'color must be an integer in the range 0-7,',
                                'or a prompter.colors color, and not {color!r}'
                            ]).format(
                                color=color
                            )
                        )
                    )
                ),
                code='m'
            ),
            """
            Set ANSI text color.

            :param color: The color to set the text (foreground) to.
            :type color: integer
            """
        )

        self.register_attr(
            'AnsiColorBack',
            lambda: lambda color: AnsiSequence(
                *(
                    [1 if color.ansi[1] else 2, 40 + color.ansi[0]]
                    if hasattr(color, 'ansi')
                    else [1 if color.ansi[1] else 2, 40 + color.rgb.ansi[0]]
                    if hasattr(color, 'rgb') and hasattr(color.rgb, 'ansi')
                    else [40 + color]
                    if color in range(8)
                    else raise_(
                        ValueError(
                            ' '.join([
                                'color must be an integer in the range 0-7,',
                                'or a prompter.colors color, and not {color!r}'
                            ]).format(
                                color=color
                            )
                        )
                    )
                ),
                code='m'
            ),
            """
            Set ANSI background color.

            :param color: The color to set the background to.
            :type color: integer
            """
        )

        self.register_attr(
            'ResetColorText',
            lambda: lambda: AnsiSequence(39, code='m'),
            """
            Resets the text (foreground) color.
            """
        )

        self.register_attr(
            'ResetColorBack',
            lambda: lambda: AnsiSequence(49, code='m'),
            """
            Resets the background color.
            """
        )

        self.register_attr(
            'Color24Text',
            lambda: lambda r, g=None, b=None: AnsiSequence(
                38,
                2,
                *(
                    [r.rgb.red, r.rgb.green, r.rgb.blue]
                    if (
                        hasattr(r, 'rgb')
                        and hasattr(r.rgb, 'red')
                        and hasattr(r.rgb, 'green')
                        and hasattr(r.rgb, 'blue')
                    )
                    else [r.red, r.green, r.blue]
                    if (
                        hasattr(r, 'red')
                        and hasattr(r, 'green')
                        and hasattr(r, 'blue')
                    )
                    else [r, g, b]
                    if (
                        r in range(256)
                        and g in range(256)
                        and b in range(256)
                    )
                    else raise_(
                        ValueError(
                            ' '.join([
                                'r must be a prompter.colors color or r, g,',
                                'and b must be integers in the range'
                                '(0-255), not {r!r}, {g!r}, {b!r}'
                            ]).format(
                                r=r,
                                g=g,
                                b=b
                            )
                        )
                    )
                ),
                code='m'
            ),
            """
            Set xterm 24-bit text (foreground) color. This can either be
            through setting individual r, g, b integer values, or can be
            through using a :py:mod:`prompter.colors` color.

            :param r: Either the :py:mod:`prompter.colors` color, or the
                integer value for the red component.
            :param g: Either the integer value for the green component or not
                needed (if r is a :py:mod:`prompter.colors` color)
            :param b: Either the integer value for the blue component or not
                needed (if r is a :py:mod:`prompter.colors` color)
            """
        )

        self.register_attr(
            'Color24Back',
            lambda: lambda r, g=None, b=None: AnsiSequence(
                48,
                2,
                *(
                    [r.rgb.red, r.rgb.green, r.rgb.blue]
                    if (
                        hasattr(r, 'rgb')
                        and hasattr(r.rgb, 'red')
                        and hasattr(r.rgb, 'green')
                        and hasattr(r.rgb, 'blue')
                    )
                    else [r.red, r.green, r.blue]
                    if (
                        hasattr(r, 'red')
                        and hasattr(r, 'green')
                        and hasattr(r, 'blue')
                    )
                    else [r, g, b]
                    if (
                        r in range(256)
                        and g in range(256)
                        and b in range(256)
                    )
                    else raise_(
                        ValueError(
                            ' '.join([
                                'r must be a prompter.colors color or r, g,',
                                'and b must be integers in the range'
                                '(0-255), not {r!r}, {g!r}, {b!r}'
                            ]).format(
                                r=r,
                                g=g,
                                b=b
                            )
                        )
                    )
                ),
                code='m'
            ),
            """
            Set xterm 24-bit background color. This can either be through
            setting individual r, g, b integer values, or can be through using
            a :py:mod:`prompter.colors` color.

            :param r: Either the :py:mod:`prompter.colors` color, or the
                integer value for the red component.
            :param g: Either the integer value for the green component or not
                needed (if r is a :py:mod:`prompter.colors` color)
            :param b: Either the integer value for the blue component or not
                needed (if r is a :py:mod:`prompter.colors` color)
            """
        )

        self.register_attr(
            'ColorText',
            lambda: lambda color: AnsiSequence(
                38,
                5,
                color.xterm
                if hasattr(color, 'xterm')
                else color.rgb.xterm
                if hasattr(color, 'rgb') and hasattr(color.rgb, 'xterm')
                else color
                if color in range(256)
                else raise_(
                    ValueError(
                        ' '.join([
                            'color must be an integer in the range (0-255)',
                            'or a prompter.colors color, not {color!r}'
                        ]).format(
                            color=color
                        )
                    )
                ),
                code='m'
            ),
            """
            Set xterm text (foreground) color. *color* is color index from 0 to
            255 or a :py:mod:`prompter.colors` color.

            :param color: Either a :py:mod:`prompter.colors` color or the 0-255
                color index.
            """
        )

        self.register_attr(
            'ColorBack',
            lambda: lambda color: AnsiSequence(
                48,
                5,
                color.xterm
                if hasattr(color, 'xterm')
                else color.rgb.xterm
                if hasattr(color, 'rgb') and hasattr(color.rgb, 'xterm')
                else color
                if color in range(256)
                else raise_(
                    ValueError(
                        ' '.join([
                            'color must be an integer in the range (0-255)',
                            'or a prompter.colors color, not {color!r}'
                        ]).format(
                            color
                        )
                    )
                ),
                code='m'
            ),
            """
            Set xterm background color. *color* is color index from 0 to 255 or
            a :py:mod:`prompter.colors` color.

            :param color: Either a :py:mod:`prompter.colors` color or the 0-255
                color index.
            """
        )


class AnsiConfig(config.Base):
    def __init__(self):
        self.register_attr(
            'seq',
            lambda: SequenceConfig(),
            SequenceConfig.__doc__
        )

        self.register_attr(
            'code',
            lambda: config.to_config({
                'erase': {
                    code.name: code
                    for code in EraseCode
                },
                'CSI': AnsiSequence.CSI,
            }),
            'Contains codes used by the ansi module.'
        )
