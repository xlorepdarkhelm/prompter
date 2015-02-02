import collections
import colorsys
import functools

from prompter import config


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
    def gen_gradient(self, color_type, other):
        used = set()
        meth = getattr(self.rgb, '_'.join(['gen', color_type, 'gradient']))
        for color in (
            getattr(rgb_color, self.simple_name)
            for rgb_color in meth(other)
        ):
            if color not in used:
                used.add(color)
                yield color

    @staticmethod
    def gen_grayscale_range(cls, start, end):
        used = set()
        for color in (
            getattr(rgb_color, cls.simple_name)
            for rgb_color in RGBColor.gen_grayscale_range(start, end)
        ):
            if color not in used:
                used.add(color)
                yield color

    def __call__(self, cls):
        cls.simple_name = self.simple_name
        cls.values = self.values
        cls.rgb = property(CubeDecorator.rgb)
        cls.__new__ = CubeDecorator.new

        cls.gen_rgb_gradient = functools.partialmethod(
            CubeDecorator.gen_gradient,
            'rgb'
        )
        cls.gen_hsv_gradient = functools.partialmethod(
            CubeDecorator.gen_gradient,
            'hsv'
        )
        cls.gen_hsl_gradient = functools.partialmethod(
            CubeDecorator.gen_gradient,
            'hsl'
        )

        cls.gen_grayscale_range = classmethod(
            CubeDecorator.gen_grayscale_range
        )

        return cls


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
    @property
    def xterm(self):
        if not hasattr(self, '_Cube6XtermColor__xterm'):
            self.__xterm = RGBColor._xterm[16:232].index(self.rgb) + 16

        return self.__xterm


class RGBMeta(type):
    @property
    def _ansi(self):
        if not hasattr(self, '_RGBMeta__ansi'):
            self.__ansi = tuple(
                self(*rgb)
                for rgb in config.colors.ansi
            )

        return self.__ansi

    @property
    def _xterm(self):
        if not hasattr(self, '_RGBMeta__xterm'):
            self.__xterm = tuple(
                self(*rgb)
                for rgb in config.colors.xterm
            )

        return self.__xterm


class RGBColor(
    collections.namedtuple('RGBColor', 'red green blue'),
    metaclass=RGBMeta
):
    @property
    def hsv(self):
        if not hasattr(self, '_RGBColor__hsv'):
            hue, saturation, value = colorsys.rgb_to_hsv(
                self.red / 255,
                self.green / 255,
                self.blue / 255,
            )

            self.__hsv = HSVColor(
                int(hue * 360),
                int(saturation * 100),
                int(value * 100)
            )

        return self.__hsv

    @property
    def hsl(self):
        if not hasattr(self, '_RGBColor__hsl'):
            hue, lightness, saturation = colorsys.rgb_to_hls(
                self.red / 255,
                self.green / 255,
                self.blue / 255,
            )

            self.__hsl = HSLColor(
                int(hue * 360),
                int(saturation * 100),
                int(lightness * 100)
            )

        return self.__hsl

    def __mul__(self, other):
        used = set()

        for hsv in self.to_HSV() * other:
            color = hsv.to_RGB()

            if color not in used:
                used.add(color)
                yield color

    @property
    def xterm(self):
        if not hasattr(self, '_RGBColor__xterm'):
            cls = type(self)

            ansi_grays = {192}
            ansi_colors1 = {128}
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
                min(good_values, key=lambda x: abs(x - self.red)),
                min(good_values, key=lambda x: abs(x - self.green)),
                min(good_values, key=lambda x: abs(x - self.blue)),
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
                    min(good_values, key=lambda x: abs(x - self.red)),
                    min(good_values, key=lambda x: abs(x - self.green)),
                    min(good_values, key=lambda x: abs(x - self.blue)),
                )

                phase1 = ansi_colors1 - cube_colors
                phase2 = ansi_colors2 | cube_colors

                if any(
                    color in fixed and any(
                        item in phase2
                        for item in fixed
                    )
                    for color in phase1
                ):
                    good_values = sorted(list(phase2))

                    fixed = RGBColor(
                        min(good_values, key=lambda x: abs(x - self.red)),
                        min(good_values, key=lambda x: abs(x - self.green)),
                        min(good_values, key=lambda x: abs(x - self.blue)),
                    )

            # print(fixed)
            self.__xterm = cls._xterm.index(fixed)

        return self.__xterm

    @classmethod
    def __to_cube(cls, red, green, blue, values):
        return (
            values.index(min(values, key=lambda x: abs(x - red))),
            values.index(min(values, key=lambda x: abs(x - green))),
            values.index(min(values, key=lambda x: abs(x - blue))),
        )

    @property
    def cube6(self):
        if not hasattr(self, '_RGBColor__cube6'):
            self.__cube6 = Cube6Color(
                *self.__to_cube(
                    self.red,
                    self.green,
                    self.blue,
                    Cube6Color.values
                )
            )

        return self.__cube6

    @property
    def cube5(self):
        if not hasattr(self, '_RGBColor__cube5'):
            self.__cube5 = Cube5Color(
                *self.__to_cube(
                    self.red,
                    self.green,
                    self.blue,
                    Cube5Color.values
                )
            )

        return self.__cube5

    @property
    def cube6_xterm(self):
        if not hasattr(self, '_RGBColor__cube6_xterm'):
            self.__cube6_xterm = Cube6XtermColor(
                *self.__to_cube(
                    self.red,
                    self.green,
                    self.blue,
                    Cube6XtermColor.values
                )
            )

        return self.__cube6_xterm

    @classmethod
    def from_grayscale(cls, shade):
        if shade not in range(101):
            raise ValueError(
                'The shade must be in the range 0-100, not {shade}'.format(
                    shade=shade
                )
            )

        value = int((shade / 100) * 255 + 0.5)

        return cls(value, value, value)

    @classmethod
    def from_ansi(cls, ndx, shift):
        if ndx not in range(8):
            raise ValueError(
                'The index value must be in the range 0-7, not {ndx}'.format(
                    ndx=ndx
                )
            )

        ndx = int(ndx) + 8 * int(bool(shift))

        return cls._ansi[ndx]

    @classmethod
    def from_xterm(cls, ndx):
        if ndx not in range(256):
            raise ValueError(
                'The index value must be in the range 0-255, not {ndx}'.format(
                    ndx=ndx
                )
            )

        return cls._xterm[int(ndx)]

    @property
    def ansi(self):
        if not hasattr(self, '_RGBColor__ansi'):
            cls = type(self)

            def get_ansi(rgb):
                if rgb in cls._ansi[:8]:
                    return cls._ansi[:8].index(rgb), False
                else:
                    return cls._ansi[8:].index(rgb), True

            good_values = [0, 128, 192, 255]

            fixed = RGBColor(
                min(good_values, key=lambda x: abs(x - self.red)),
                min(good_values, key=lambda x: abs(x - self.green)),
                min(good_values, key=lambda x: abs(x - self.blue)),
            )

            if (
                192 in fixed
                and not (
                    fixed.red == fixed.green == fixed.blue
                )
            ):
                good_values = [0, 128, 255]

                fixed = RGBColor(
                    min(good_values, key=lambda x: abs(x - self.red)),
                    min(good_values, key=lambda x: abs(x - self.green)),
                    min(good_values, key=lambda x: abs(x - self.blue)),
                )

            if 128 in fixed and 255 in fixed:
                good_values = [0, 255]

                fixed = RGBColor(
                    min(good_values, key=lambda x: abs(x - self.red)),
                    min(good_values, key=lambda x: abs(x - self.green)),
                    min(good_values, key=lambda x: abs(x - self.blue)),
                )

            self.__ansi = get_ansi(fixed)

        return self.__ansi

    def gen_hsv_gradient(self, other):
        yield from (
            hsv_color.rgb
            for hsv_color in self.hsv.gen_hsv_gradient(other)
        )

    def gen_hsl_gradient(self, other):
        yield from (
            hsl_color.rgb
            for hsl_color in self.hsl.gen_hsl_gradient(other)
        )

    def gen_rgb_gradient(self, other):
        if isinstance(
            other,
            (HSVColor, HSLColor, Cube6Color, Cube5Color, Cube6XtermColor)
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

    @classmethod
    def gen_grayscale_range(cls, start, end):
        shade_start = cls.from_grayscale(start)
        shade_end = cls.from_grayscale(end)
        yield from shade_start.gen_rgb_gradient(shade_end)

    @classmethod
    def gen_xterm_grayscale_range(cls, start, end):
        used = set()

        for shade in cls.gen_grayscale_range(start, end):
            ndx = int(shade.red / (255 / 25) + .5) - 1

            if ndx < 0:
                ret = RGBColor(0, 0, 0)
            elif ndx >= 24:
                ret = RGBColor(255, 255, 255)
            else:
                val = list(range(8, 247, 10))[ndx]
                ret = RGBColor(val, val, val)

            if ret not in used:
                used.add(ret)
                yield ret


class HSVColor(collections.namedtuple('HSVColor', 'hue saturation value')):
    @property
    def rgb(self):
        if not hasattr(self, '_HSVColor__rgb'):
            red, green, blue = colorsys.hsv_to_rgb(
                self.hue / 360,
                self.saturation / 100,
                self.value / 100,
            )

            self.__rgb = RGBColor(
                int(red * 255),
                int(green * 255),
                int(blue * 255),
            )

        return self.__rgb

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

    def dist_saturation(self, saturation):
        if self.saturation < saturation:
            return saturation - self.saturation

        else:
            return -(self.saturation - saturation)

    def dist_value(self, value):
        if self.value < value:
            return value - self.value

        else:
            return -(self.value - value)

    def gen_rgb_gradient(self, other):
        yield from (
            rgb_color.hsv
            for rgb_color in self.rgb.gen_rgb_gradient(other)
        )

    def gen_hsl_gradient(self, other):
        yield from (
            hsl_color.rgb.hsv
            for hsl_color in self.rgb.hsl.gen_hsl_gradient(other)
        )

    def gen_hsv_gradient(self, other):
        if isinstance(other, RGBColor):
            other = other.hsv

        elif isinstance(
            other,
            (HSLColor, Cube6Color, Cube5Color, Cube6XtermColor)
        ):
            other = other.rgb.hsv

        elif not isinstance(other, HSVColor) and other < 0:
            other = self.decr_hue(-1 * other)

        elif not isinstance(other, HSVColor):
            other = self.incr_hue(other)

        dist_hue = self.dist_hue(other.hue)
        dist_saturation = self.dist_saturation(other.saturation)
        dist_value = self.dist_value(other.value)

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


class HSLColor(collections.namedtuple('HSLColor', 'hue saturation lightness')):
    @property
    def rgb(self):
        if not hasattr(self, '_HSLColor__rgb'):
            red, green, blue = colorsys.hls_to_rgb(
                self.hue / 360,
                self.lightness / 100,
                self.saturation / 100,
            )

            self.__rgb = RGBColor(
                int(red * 255),
                int(green * 255),
                int(blue * 255),
            )

        return self.__rgb

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

    def dist_saturation(self, saturation):
        if self.saturation < saturation:
            return saturation - self.saturation

        else:
            return -(self.saturation - saturation)

    def dist_lightness(self, lightness):
        if self.lightness < lightness:
            return lightness - self.lightness

        else:
            return -(self.lightness - lightness)

    def gen_rgb_gradient(self, other):
        yield from (
            rgb_color.hsl
            for rgb_color in self.rgb.gen_rgb_gradient(other)
        )

    def gen_hsv_gradient(self, other):
        yield from (
            hsv_color.rgb.hsl
            for hsv_color in self.rgb.hsv.gen_hsv_gradient(other)
        )

    def gen_hsl_gradient(self, other):
        if isinstance(other, RGBColor):
            other = other.hsl

        elif isinstance(
            other,
            (HSVColor, Cube6Color, Cube5Color, Cube6XtermColor)
        ):
            other = other.rgb.hsl

        elif not isinstance(other, HSLColor) and other < 0:
            other = self.decr_hue(-1 * other)

        elif not isinstance(other, HSLColor):
            other = self.incr_hue(other)

        dist_hue = self.dist_hue(other.hue)
        dist_saturation = self.dist_saturation(other.saturation)
        dist_lightness = self.dist_lightness(other.lightness)

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
            lambda: RGBColor.from_ansi,
            RGBColor.from_ansi.__doc__
        )

        self.register_attr(
            'from_xterm',
            lambda: RGBColor.from_xterm,
            RGBColor.from_xterm.__doc__
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
            'from_grayscale',
            lambda: RGBColor.from_grayscale,
            RGBColor.from_grayscale.__doc__
        )

        self.register_attr(
            'from_cube6_xterm',
            lambda: lambda r, g, b: Cube6XtermColor(r, g, b).rgb,
            Cube6XtermColor.__doc__
        )

        self.register_attr(
            'gen_grayscale_range',
            lambda: RGBColor.gen_grayscale_range,
            RGBColor.gen_grayscale_range.__doc__
        )

        self.register_attr(
            'gen_xterm_grayscale_range',
            lambda: RGBColor.gen_xterm_grayscale_range,
            RGBColor.gen_xterm_grayscale_range.__doc__
        )

        self.register_attr(
            'gen_cube6_grayscale_range',
            lambda: Cube6Color.gen_grayscale_range,
            Cube6Color.gen_grayscale_range.__doc__
        )

        self.register_attr(
            'gen_cube5_grayscale_range',
            lambda: Cube5Color.gen_grayscale_range,
            Cube5Color.gen_grayscale_range.__doc__
        )

        self.register_attr(
            'gen_cube6_xterm_grayscale_range',
            lambda: Cube6XtermColor.gen_grayscale_range,
            Cube6XtermColor.gen_grayscale_range.__doc__
        )
