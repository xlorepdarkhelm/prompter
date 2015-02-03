import collections
import colorsys
import functools

from prompter import config


class ColorDecorator:
    props = {
        'rgb',
        'hsv',
        'hsl',
        'ansi',
        'xterm',
        'grayscale',
        'cube6',
        'cube5',
        'cube6_xterm',
    }

    grads = {
        'rgb',
        'hsv',
        'hsl',
        'grayscale',
    }

    def __init__(self, short_name, base_prop=None):
        self.short_name = short_name
        self.base_prop = base_prop

    @staticmethod
    def prop_meth(name, base_prop, self):
        cls = type(self)
        if not hasattr(
            self, '_{name}__{prop}'.format(name=cls.__name__, prop=name)
        ):
            setattr(
                self,
                ''.join(['__', name]),
                getattr(getattr(self, base_prop), name)
            )

        return getattr(self, ''.join(['__', name]))

    @staticmethod
    def gen_gradient(self, short_name, color_type, other):
        used = set()
        meth = getattr(
            getattr(self, color_type),
            '_'.join(['gen', color_type, 'gradient'])
        )

        for color in (
            getattr(sub_color, short_name)
            for sub_color in meth(other)
        ):
            if color not in used:
                used.add(color)
                yield color

    def __call__(self, cls):
        if self.base_prop is not None:
            my_props = {
                prop
                for prop in ColorDecorator.props
                if hasattr(cls, prop)
            }

            my_props.add(self.short_name)

            for prop in ColorDecorator.props - my_props:
                setattr(
                    cls,
                    prop,
                    property(
                        functools.partial(
                            ColorDecorator.prop_meth,
                            prop,
                            self.base_prop
                        )
                    )
                )

        my_grads = {
            grad
            for grad in ColorDecorator.grads
            if hasattr(cls, '_'.join(['gen', grad, 'gradient']))
        }

        for grad in ColorDecorator.grads - my_grads:
            grad_name = '_'.join(['gen', grad, 'gradient'])
            setattr(
                cls,
                grad_name,
                functools.partialmethod(
                    ColorDecorator.gen_gradient,
                    self.short_name,
                    grad
                )
            )

        return cls


class CubeDecorator:
    def __init__(self, simple_name, *values):
        self.simple_name = simple_name
        self.values = values

    @staticmethod
    def rgb(self):
        cls = type(self)
        if not hasattr(self, '_{name}__rgb'.format(name=cls.__name__)):
            self.__rgb = RGBColor(
                cls.values[self.red],
                cls.values[self.green],
                cls.values[self.blue]
            )
        return self.__rgb

    @staticmethod
    def check_value(name, value, values):
        if value not in range(len(values)):
            raise ValueError(
                '{name} must be in range 0-{max}, not {val}.'.format(
                    name=name,
                    max=len(values) - 1,
                    val=value
                )
            )

    @staticmethod
    def new(cls, red, green, blue):
        CubeDecorator.check_value('red', red, cls.values)
        CubeDecorator.check_value('green', green, cls.values)
        CubeDecorator.check_value('blue', blue, cls.values)

        return super(cls, cls).__new__(cls, red, green, blue)

    @staticmethod
    def from_rgb(cls, rgb):
        red = cls.values.index(
            min(cls.values, key=lambda x: abs(x - rgb.red))
        )
        green = cls.values.index(
            min(cls.values, key=lambda x: abs(x - rgb.green))
        )
        blue = cls.values.index(
            min(cls.values, key=lambda x: abs(x - rgb.blue))
        )

        return cls(red, green, blue)

    def __call__(self, cls):
        cls.simple_name = self.simple_name
        cls.values = self.values
        cls.rgb = property(CubeDecorator.rgb)
        cls.__new__ = CubeDecorator.new

        cls.from_rgb = classmethod(CubeDecorator.from_rgb)

        return ColorDecorator(self.simple_name, 'rgb')(cls)


class CubeMeta(type):
    def __new__(meta, name, bases, ns):
        bases = bases + (collections.namedtuple(name, 'red green blue'), )

        return type.__new__(meta, name, bases, ns)


@CubeDecorator('cube6', 0x00, 0x33, 0x66, 0x99, 0xcc, 0xff)
class Cube6Color(metaclass=CubeMeta):
    pass


@CubeDecorator('cube5', 0x00, 0x40, 0x80, 0xbf, 0xff)
class Cube5Color(metaclass=CubeMeta):
    pass


@CubeDecorator('cube6_xterm', 0, 95, 135, 175, 215, 255)
class Cube6XtermColor(metaclass=CubeMeta):
    pass


@ColorDecorator('grayscale', 'rgb')
class GrayscaleColor(collections.namedtuple('GrayscaleColor', 'index')):
    def __new__(cls, index):
        if index not in range(101):
            raise ValueError(
                ' '.join([
                    'The index must be an integer value between 0-100,',
                    'not {value!r}'
                ]).format(
                    value=index
                )
            )

        return super().__new__(cls, index)

    @property
    def rgb(self):
        if not hasattr(self, '_GrayscaleColor__rgb'):
            val = int(self.index / 100 * 255 + 0.5)
            self.__rgb = RGBColor(val, val, val)

        return self.__rgb

    @classmethod
    def from_rgb(cls, rgb):
        return cls(
            int(
                (
                    0.21 * rgb.red
                    + 0.72 * rgb.green
                    + 0.07 * rgb.blue
                ) * 100 / 255 + 0.5
            )
        )

    def gen_grayscale_gradient(self, other):
        if isinstance(
            other,
            (
                HSVColor,
                HSLColor,
                Cube6Color,
                Cube5Color,
                Cube6XtermColor,
                AnsiColor,
                XtermColor,
                RGBColor,
            )
        ):
            other = other.grayscale

        elif not isinstance(other, GrayscaleColor):
            other = GrayscaleColor(other)

        dist = other.index - self.index
        delta = dist // abs(dist)

        used = set()

        for ndx in range(self.index, self.index + dist + delta, delta):
            color = GrayscaleColor(ndx)
            if color not in used:
                used.add(color)
                yield color


class AnsiMeta(type):
    @property
    def _reftbl(self):
        if not hasattr(self, '_AnsiMeta__reftbl'):
            self.__reftbl = tuple(
                RGBColor(*rgb)
                for rgb in config.colors.ansi
            )

        return self.__reftbl


@ColorDecorator('ansi', 'rgb')
class AnsiColor(
    collections.namedtuple('AnsiColor', 'index shift'),
    metaclass=AnsiMeta
):
    def __new__(cls, index, shift):
        if index not in range(8):
            raise ValueError(
                'The index value must be in the range 0-7, not {ndx}'.format(
                    ndx=index
                )
            )

        return super().__new__(cls, int(index), bool(shift))

    @property
    def rgb(self):
        if not hasattr(self, '_AnsiColor__rgb'):
            cls = type(self)
            self.__rgb = cls._reftbl[self.index + 8 * int(self.shift)]

        return self.__rgb

    @classmethod
    def from_rgb(cls, rgb):
        grays = {192}
        colors1 = {0, 128}
        colors2 = {0, 255}

        def get_ansi(rgb_val):
            if rgb_val in cls._reftbl[:8]:
                return cls._reftbl[:8].index(rgb_val), False

            else:
                return cls._reftbl[8:].index(rgb_val), True

        good_values = sorted(list(grays | colors1 | colors2))

        fixed = RGBColor(
            min(good_values, key=lambda x: abs(x - rgb.red)),
            min(good_values, key=lambda x: abs(x - rgb.green)),
            min(good_values, key=lambda x: abs(x - rgb.blue)),
        )

        if (
            any(color in grays for color in fixed)
            and (
                fixed.red != fixed.green or
                fixed.red != fixed.blue or
                fixed.green != fixed.blue
            )
        ):
            good_values = sorted(list(colors1 | colors2))

            fixed = RGBColor(
                min(good_values, key=lambda x: abs(x - rgb.red)),
                min(good_values, key=lambda x: abs(x - rgb.green)),
                min(good_values, key=lambda x: abs(x - rgb.blue)),
            )

        exclusive1 = colors1 - colors2
        exclusive2 = colors2 - colors1

        if any(
            color in fixed and any(
                item in exclusive2
                for item in fixed
            )
            for color in exclusive1
        ):
            good_values = sorted(list(colors2))

            fixed = RGBColor(
                min(good_values, key=lambda x: abs(x - rgb.red)),
                min(good_values, key=lambda x: abs(x - rgb.green)),
                min(good_values, key=lambda x: abs(x - rgb.blue)),
            )

        return cls(*get_ansi(fixed))


class XtermMeta(type):
    @property
    def _reftbl(self):
        if not hasattr(self, '_XtermMeta__reftbl'):
            self.__reftbl = tuple(
                RGBColor(*rgb)
                for rgb in config.colors.xterm
            )

        return self.__reftbl


@ColorDecorator('xterm', 'rgb')
class XtermColor(
    collections.namedtuple('XtermColor', 'index'),
    metaclass=XtermMeta
):
    def __new__(cls, index):
        if index not in range(len(cls._reftbl)):
            raise ValueError(
                ' '.join([
                    'The index must be an integer value between 0-{max},',
                    'not {value!r}'
                ]).format(
                    max=len(cls._reftbl) - 1,
                    value=index
                )
            )

        return super().__new__(cls, index)

    @property
    def rgb(self):
        if not hasattr(self, '_XtermColor__rgb'):
            cls = type(self)
            self.__rgb = cls._reftbl[self.index]

        return self.__rgb

    @classmethod
    def from_rgb(cls, rgb):
        ansi_grays = {192}
        ansi_colors1 = {0, 128}
        ansi_colors2 = {0, 255}
        cube_colors = set(Cube6XtermColor.values)
        grayscale = set(range(8, 239, 10))

        good_values = sorted(list(
            ansi_grays
            | ansi_colors1
            | ansi_colors2
            | cube_colors
            | grayscale
        ))

        fixed = RGBColor(
            min(good_values, key=lambda x: abs(x - rgb.red)),
            min(good_values, key=lambda x: abs(x - rgb.green)),
            min(good_values, key=lambda x: abs(x - rgb.blue)),
        )

        grays = (
            (ansi_grays | grayscale)
            - (ansi_colors1 | ansi_colors2 | cube_colors)
        )

        if (
            any(color in grays for color in fixed)
            and (
                fixed.red != fixed.green or
                fixed.red != fixed.blue or
                fixed.green != fixed.blue
            )
        ):
            good_values = sorted(
                list(ansi_colors1 | ansi_colors2 | cube_colors)
            )

            fixed = RGBColor(
                min(good_values, key=lambda x: abs(x - rgb.red)),
                min(good_values, key=lambda x: abs(x - rgb.green)),
                min(good_values, key=lambda x: abs(x - rgb.blue)),
            )

        exclusive1 = ansi_colors1 - (ansi_colors2 | cube_colors)
        exclusive2 = (ansi_colors2 | cube_colors) - ansi_colors1

        if any(
            color in fixed and any(
                item in exclusive2
                for item in fixed
            )
            for color in exclusive1
        ):
            good_values = sorted(list(ansi_colors2 | cube_colors))

            fixed = RGBColor(
                min(good_values, key=lambda x: abs(x - rgb.red)),
                min(good_values, key=lambda x: abs(x - rgb.green)),
                min(good_values, key=lambda x: abs(x - rgb.blue)),
            )

        return cls(cls._reftbl.index(fixed))


@ColorDecorator('rgb')
class RGBColor(collections.namedtuple('RGBColor', 'red green blue')):
    @property
    def hsv(self):
        if not hasattr(self, '_RGBColor__hsv'):
            self.__hsv = HSVColor.from_rgb(self)

        return self.__hsv

    @property
    def hsl(self):
        if not hasattr(self, '_RGBColor__hsl'):
            self.__hsl = HSLColor.from_rgb(self)

        return self.__hsl

    @property
    def xterm(self):
        if not hasattr(self, '_RGBColor__xterm'):
            self.__xterm = XtermColor.from_rgb(self)

        return self.__xterm

    @property
    def ansi(self):
        if not hasattr(self, '_RGBColor__ansi'):
            self.__ansi = AnsiColor.from_rgb(self)

        return self.__ansi

    @property
    def grayscale(self):
        if not hasattr(self, '_RGBColor__grayscale'):
            self.__grayscale = GrayscaleColor.from_rgb(self)

        return self.__grayscale

    @property
    def cube6(self):
        if not hasattr(self, '_RGBColor__cube6'):
            self.__cube6 = Cube6Color.from_rgb(self)

        return self.__cube6

    @property
    def cube5(self):
        if not hasattr(self, '_RGBColor__cube5'):
            self.__cube5 = Cube5Color.from_rgb(self)

        return self.__cube5

    @property
    def cube6_xterm(self):
        if not hasattr(self, '_RGBColor__cube6_xterm'):
            self.__cube6_xterm = Cube6XtermColor.from_rgb(self)

        return self.__cube6_xterm

    @classmethod
    def from_hsv(cls, hsv):
        red, green, blue = colorsys.hsv_to_rgb(
            hsv.hue / 360,
            hsv.saturation / 100,
            hsv.value / 100,
        )

        return cls(
            int(red * 255),
            int(green * 255),
            int(blue * 255),
        )

    @classmethod
    def from_hsl(cls, hsl):
        red, green, blue = colorsys.hls_to_rgb(
            hsl.hue / 360,
            hsl.lightness / 100,
            hsl.saturation / 100,
        )

        return cls(
            int(red * 255),
            int(green * 255),
            int(blue * 255),
        )

    def gen_rgb_gradient(self, other):
        if isinstance(
            other,
            (
                HSVColor,
                HSLColor,
                Cube6Color,
                Cube5Color,
                Cube6XtermColor,
                AnsiColor,
                XtermColor,
                GrayscaleColor,
            )
        ):
            other = other.rgb

        elif not isinstance(other, RGBColor):
            raise ValueError(
                ' '.join([
                    'The given value must be a RGBColor, HSVColor,',
                    'or HSLColor, not {other_type}'
                ]).format(
                    other_type=type(other)
                )
            )

        dist_value = lambda src, dst: dst - src

        dist_red = dist_value(self.red, other.red)
        dist_green = dist_value(self.green, other.green)
        dist_blue = dist_value(self.blue, other.blue)

        denom = max(abs(dist_red), abs(dist_green), abs(dist_blue))

        delta_red = dist_red / denom
        delta_green = dist_green / denom
        delta_blue = dist_blue / denom

        red = self.red
        green = self.green
        blue = self.blue

        used = {self}
        yield self

        for i in range(denom):
            red += delta_red
            green += delta_green
            blue += delta_blue

            color = RGBColor(int(red), int(green), int(blue))
            if color not in used:
                used.add(color)
                yield color


@ColorDecorator('hsv', 'rgb')
class HSVColor(collections.namedtuple('HSVColor', 'hue saturation value')):
    @property
    def rgb(self):
        if not hasattr(self, '_HSVColor__rgb'):
            self.__rgb = RGBColor.from_hsv(self)

        return self.__rgb

    @classmethod
    def from_rgb(cls, rgb):
        hue, saturation, value = colorsys.rgb_to_hsv(
            rgb.red / 255,
            rgb.green / 255,
            rgb.blue / 255,
        )

        return cls(
            int(hue * 360),
            int(saturation * 100),
            int(value * 100)
        )

    def incr_hue(self, hue):
        hue += self.hue
        while hue >= 360:
            hue -= 360

        return HSVColor(int(hue + 0.5), self.saturation, self.value)

    def decr_hue(self, hue):
        hue -= self.hue
        while hue < 0:
            hue += 360

        return HSVColor(int(hue + 0.5), self.saturation, self.value)

    def dist_hue(self, hue):
        dist1 = self.hue - hue
        while dist1 < 0:
            dist1 += 360

        dist2 = hue - self.hue
        while dist2 < 0:
            dist2 += 360

        return -dist1 if dist1 < dist2 else dist2

    def gen_hsv_gradient(self, other):
        if isinstance(
            other,
            (
                HSLColor,
                Cube6Color,
                Cube5Color,
                Cube6XtermColor,
                RGBColor,
                XtermColor,
                AnsiColor,
                GrayscaleColor,
            )
        ):
            other = other.hsv

        elif not isinstance(other, HSVColor) and other < 0:
            other = self.decr_hue(-1 * other)

        elif not isinstance(other, HSVColor):
            other = self.incr_hue(other)

        dist_hue = self.dist_hue(other.hue)
        dist_saturation = other.saturation - self.saturation
        dist_value = other.value - self.value

        denom = max(abs(dist_hue), abs(dist_saturation), abs(dist_value))

        delta_hue = dist_hue / denom
        delta_saturation = dist_saturation / denom
        delta_value = dist_value / denom

        hue = self.hue
        saturation = self.saturation
        value = self.value

        used = {self}
        yield self

        for i in range(denom):
            hue += delta_hue
            saturation += delta_saturation
            value += delta_value

            color = HSVColor(int(hue), int(saturation), int(value))
            if color not in used:
                used.add(color)
                yield color


@ColorDecorator('hsl', 'rgb')
class HSLColor(collections.namedtuple('HSLColor', 'hue saturation lightness')):
    @property
    def rgb(self):
        if not hasattr(self, '_HSLColor__rgb'):
            self.__rgb = RGBColor.from_hsl(self)

        return self.__rgb

    @classmethod
    def from_rgb(cls, rgb):
        hue, lightness, saturation = colorsys.rgb_to_hls(
            rgb.red / 255,
            rgb.green / 255,
            rgb.blue / 255,
        )

        return cls(
            int(hue * 360),
            int(saturation * 100),
            int(lightness * 100)
        )

    def incr_hue(self, hue):
        hue += self.hue
        while hue >= 360:
            hue -= 360

        return HSLColor(int(hue + 0.5), self.saturation, self.lightness)

    def decr_hue(self, hue):
        hue -= self.hue
        while hue < 0:
            hue += 360

        return HSLColor(int(hue + 0.5), self.saturation, self.lightness)

    def dist_hue(self, hue):
        dist1 = self.hue - hue
        while dist1 < 0:
            dist1 += 360

        dist2 = hue - self.hue
        while dist2 < 0:
            dist2 += 360

        return -dist1 if dist1 < dist2 else dist2

    def gen_hsl_gradient(self, other):
        if isinstance(
            other,
            (
                HSVColor,
                Cube6Color,
                Cube5Color,
                Cube6XtermColor,
                RGBColor,
                XtermColor,
                AnsiColor,
                GrayscaleColor,
            )
        ):
            other = other.hsl

        elif not isinstance(other, HSLColor) and other < 0:
            other = self.decr_hue(-1 * other)

        elif not isinstance(other, HSLColor):
            other = self.incr_hue(other)

        dist_hue = self.dist_hue(other.hue)
        dist_saturation = other.saturation - self.saturation
        dist_lightness = other.lightness - self.lightness

        denom = max(abs(dist_hue), abs(dist_saturation), abs(dist_lightness))

        delta_hue = dist_hue / denom
        delta_saturation = dist_saturation / denom
        delta_lightness = dist_lightness / denom

        hue = self.hue
        saturation = self.saturation
        lightness = self.lightness

        used = {self}
        yield self

        for i in range(denom):
            hue += delta_hue
            saturation += delta_saturation
            lightness += delta_lightness

            color = HSLColor(int(hue), int(saturation), int(lightness))
            if color not in used:
                used.add(color)
                yield color


class ColorConfig(config.Base):
    def __init__(self):
        for name, value in config.colors.web.items():
            self.register_attr(
                name,
                functools.partial(
                    lambda r, g, b: RGBColor(r, g, b),
                    *value
                ),
                'The {name} color'.format(name=name)
            )

        self.register_attr(
            'from_rgb',
            lambda: lambda r, g, b: RGBColor(r, g, b),
            RGBColor.__doc__
        )

        self.register_attr(
            'from_hsv',
            lambda: lambda h, s, v: HSVColor(h, s, v).rgb,
            HSVColor.__doc__
        )

        self.register_attr(
            'from_hsl',
            lambda: lambda h, s, l: HSLColor(h, s, l).rgb,
            HSLColor.__doc__
        )

        self.register_attr(
            'from_ansi',
            lambda: lambda i, s: AnsiColor(i, s).rgb,
            AnsiColor.__doc__
        )

        self.register_attr(
            'from_xterm',
            lambda: lambda i: XtermColor(i).rgb,
            XtermColor.__doc__
        )

        self.register_attr(
            'from_grayscale',
            lambda: lambda i: GrayscaleColor(i).rgb,
            GrayscaleColor.__doc__
        )

        self.register_attr(
            'from_cube6',
            lambda: lambda r, g, b: Cube6Color(r, g, b).rgb,
            Cube6Color.__doc__
        )

        self.register_attr(
            'from_cube5',
            lambda: lambda r, g, b: Cube5Color(r, g, b).rgb,
            Cube5Color.__doc__
        )

        self.register_attr(
            'from_cube6_xterm',
            lambda: lambda r, g, b: Cube6XtermColor(r, g, b).rgb,
            Cube6XtermColor.__doc__
        )
