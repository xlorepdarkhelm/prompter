import enum
import functools
import gzip
import os
import sys

import appdirs
import pkg_resources
import yaml

SEP = '/'
NOT_LOADED = '<Not Loaded>'


@enum.unique
class FileExt(enum.Enum):
    YAML = 'yaml'
    COMPRESSED = 'gz'


@enum.unique
class PathName(enum.Enum):
    CONFIG = 'config'
    DEFAULT = 'default'


def is_set(elem):
    return any(
        isinstance(elem, good_type)
        for good_type in {
            set,
            frozenset
        }
    ) or all(
        hasattr(elem, member)
        for member in {
            'isdisjoint',
            'issubset',
            'issuperset',
            'union',
            'intersection',
            'difference',
            'symmetric_difference',
        }
    )


def is_list(elem):
    return any(
        isinstance(elem, good_type)
        for good_type in {
            list,
            tuple,
        }
    ) or (
        not any(
            isinstance(elem, bad_type)
            for bad_type in {
                str,
                bytes,
                bytearray,
                memoryview,
            }
        ) and hasattr(elem, '__getitem__')
    )


def is_dict(elem):
    return any(
        isinstance(elem, good_type)
        for good_type in {
            dict
        }
    ) or hasattr(elem, 'items')


def parse_element(elem):
    if isinstance(elem, BaseConfig):
        ret = elem

    elif is_dict(elem):
        ret = DictConfig(elem)

    elif is_set(elem):
        ret = frozenset(
            parse_element(value)
            for value in elem
        )

    elif is_list(elem):
        ret = tuple(
            parse_element(value)
            for value in elem
        )

    else:
        ret = elem

    return ret


def unpack_element(elem):
    if isinstance(elem, BaseConfig):
        ret = {
            key: unpack_element(getattr(elem, str(key)))
            for key in elem
        }

    elif is_dict(elem):
        ret = {
            key: unpack_element(value)
            for key, value in elem.items()
        }

    elif is_set(elem):
        ret = {
            unpack_element(value)
            for value in elem
        }

    elif is_list(elem):
        ret = [
            unpack_element(value)
            for value in elem
        ]

    else:
        ret = elem

    return ret


def yaml_read(filepath, resource=None, compressed=False, default_path=None):
    has_root = filepath.startswith(SEP)
    _load = lambda f: yaml.safe_load(f)

    if resource is not None and compressed:
        raise RuntimeError(
            'If the resource is specified, the file cannot be compressed.'
        )

    if resource is None:
        filename = os.path.basename(filepath)

    else:
        filename = filepath.split(SEP)[-1]

    split_filename = filename.split('.')

    ext_pos = -1

    if (
        compressed
        and split_filename[ext_pos] != FileExt.COMPRESSED.value
    ):
        raise RuntimeError(
            ' '.join([
                'Invalid compressed filename format: {filepath}',
                'must end in .{yaml}.{compressed}',
            ]).format(
                filepath=filepath,
                yaml=FileExt.YAML.value,
                compressed=FileExt.COMPRESSED.value,
            )
        )
    elif compressed:
        ext_pos -= 1

    if split_filename[ext_pos] != FileExt.YAML.value:
        raise RuntimeError(
            ' '.join([
                'Invalid filename format: {filepath}',
                'must end in .{yaml}[.{compressed}]',
            ]).format(
                filepath=filepath,
                yaml=FileExt.YAML.value,
                compressed=FileExt.COMPRESSED.value,
            )
        )

    if default_path is not None and resource is None:
        raise RuntimeError(
            ' '.join([
                'The default path absolutely requires a'
                'resource to be defined.',
            ])
        )

    if default_path is not None:
        base_path = appdirs.site_config_dir('prompter')

        filepath = os.path.join(
            base_path,
            '.'.join([
                ''.join([
                    SEP if has_root else '',
                    os.path.join(*filepath.split(SEP))
                ]),
                FileExt.COMPRESSED.value
            ])
        )
        compressed = True

        if not os.path.exists(filepath):
            default_filepath = SEP.join([
                PathName.DEFAULT.value,
                default_path,
                filename
            ])

            rebuilt_path = ''

            for folder in (
                sub
                for sub in filepath.split(os.path.sep)
                if sub != '.'.join([filename, FileExt.COMPRESSED.value])
            ):
                rebuilt_path = ''.join([rebuilt_path, os.path.sep, folder])
                if not os.path.exists(rebuilt_path):
                    os.mkdir(rebuilt_path)

            inp = pkg_resources.resource_string(resource, default_filepath)

            with gzip.open(filepath, 'wb') as out:
                out.write(inp)

    if resource is None:
        filepath = os.path.join(*filepath.split(SEP))

        if has_root:
            filepath = ''.join([SEP, filepath])

    if resource is not None and default_path is None:
        inp = pkg_resources.resource_stream(resource, filepath)

        if compressed:
            inp = str(gzip.decompress(inp.read()), 'utf-8')

        data = _load(inp)

    elif compressed:
        with gzip.open(filepath) as inp:
            data = _load(inp)

    else:
        with open(filepath) as inp:
            data = _load(inp)

    return parse_element(data)


def yaml_write(filepath, data, compressed=False):
    has_root = filepath.startswith(SEP)

    yaml_dump_params = {
        'default_flow_stype': False,
        'indent': 4,
        'width': sys.maxsize,
    }

    _dump = lambda d: bytes(yaml.safedump(d, **yaml_dump_params), 'utf-8')

    filename = os.path.basename(filepath)

    split_filename = filename.split('.')

    ext_addition = ''

    ext_pos = -1

    if (
        compressed
        and split_filename[ext_pos] != FileExt.COMPRESSED.value
    ):
        ext_addition = FileExt.COMPRESSED.value

    elif compressed:
        ext_pos -= 1

    if split_filename[ext_pos] != FileExt.YAML.value:
        ext_addition = '.'.join([FileExt.YAML.value, ext_addition])

    filepath = '.'.join([
        ''.join([
            SEP if has_root else '',
            os.path.join(*filepath.split(SEP))
        ]),
        ext_addition
    ]).rstrip('.')

    data_bytes = _dump(data)

    if compressed:
        with gzip.open(filepath, 'wb') as out:
            out.write(data_bytes)

    else:
        with open(filepath, 'wb') as out:
            out.write(data_bytes)


class BaseConfig:
    @property
    def __dict__(self):
        ret = vars(super()) if hasattr(super(), '__dict__') else {}

        ret.update({
            entry: (
                self.__internal_dict[entry]
                if entry in self.__internal_dict
                else NOT_LOADED
            )
            for entry in self.__attr_set - self.bad_names
        })

        return ret

    def __repr__(self):
        return repr(vars(self))

    def __getitem__(self, key):
        ret = vars(self)[key]

        if ret == NOT_LOADED:
            ret = getattr(self, str(key))

        return ret

    def __contains__(self, key):
        return key in vars(self)

    def __str__(self):
        return str(vars(self))

    def __sizeof__(self):
        return sys.getsizeof(vars(self))

    def __len__(self):
        return len(vars(self))

    def __iter__(self):
        yield from vars(self)

    def __eq__(self, other):
        return vars(self) == other

    def __ne__(self, other):
        return vars(self) != other

    def keys(self):
        yield from self

    def values(self):
        for key in self:
            try:
                yield self[key]

            except AttributeError:
                yield NOT_LOADED

    def items(self):
        for key in self:
            try:
                yield (key, self[key])

            except AttributeError:
                yield (key, NOT_LOADED)

    def __dir__(self):
        my_vars = set(vars(self))
        skips = self.bad_names | my_vars

        yield from (
            attr
            for attr in dir(type(self))
            if (
                attr not in skips
                and not (
                    attr.startswith('_')
                    and not attr.startswith('__')
                    and hasattr(self, str(attr)[1:])
                )
                and hasattr(self, str(attr))
            )
        )

        yield from my_vars

    def __new__(cls, *args, **kwargs):
        if hasattr(cls, '__factory_subclass'):
            return super().__new__(*args, **kwargs)

        else:
            new_cls_name = cls.__name__
            new_cls = type(new_cls_name, (cls, ), {
                '__module__': '.'.join([
                    cls.__module__,
                    cls.__name__,
                    'subclass'
                ]),
                '__factory_subclass': True,
                '__doc__': '\n'.join([
                    'Factory-generated specialized subclass.',
                    cls.__doc__ if cls.__doc__ is not None else ''
                ])
            })
            return super().__new__(new_cls)

    @property
    def bad_names(self):
        if 'bad_names' not in self.__data:
            self.bad_names = {
                'bad_names',
                'register_attr',
            } | {
                ''.join(['_BaseConfig', attr])
                for attr in {
                    '__attr_data',
                    '__attr_set',
                    '__data',
                    '__internal_dict',
                }
            }

        return self.__data['bad_names']

    @bad_names.setter
    def bad_names(self, new_bad_names):
        self.__data['bad_names'] = new_bad_names

    def copy(self):
        return vars(self).copy()

    def get(self, key, default=None):
        return vars(self).get(key, default)

    def deepcopy(self):
        return unpack_element(self)

    @property
    def __data(self):
        if not hasattr(self, '_BaseConfig__attr_data'):
            self.__attr_data = {}

        return self.__attr_data

    @property
    def __internal_dict(self):
        if 'internal_dict' not in self.__data:
            self.__data['internal_dict'] = {}

        return self.__data['internal_dict']

    @property
    def __attr_set(self):
        if 'attr_set' not in self.__data:
            self.__data['attr_set'] = set()

        return self.__data['attr_set']

    def register_attr(self, name, func, doc=None, setable=False):
        if doc is None:
            doc = 'The {name} attribute.'.format(name=name)

        if setable:
            def get(self):
                if name not in self.__internal_dict:
                    raise AttributeError(
                        '{name} attribute does not exist'.format(
                            name=name
                        )
                    )

                return self.__internal_dict[name]

            def set(self, value):
                if name in self.__internal_dict:
                    raise AttributeError(
                        "can't change {name} attribute".format(
                            name=name
                        )
                    )

                self.__internal_dict[name] = func(value)

            attr_func = property(get, set, doc=doc)

        else:
            def get(self):
                if name not in self.__internal_dict:
                    self.__internal_dict[name] = func()

                return self.__internal_dict[name]

            attr_func = property(get, doc=doc)

        setattr(type(self), str(name), attr_func)
        self.__attr_set.add(name)


class DictConfig(BaseConfig):
    def __init__(self, source):
        for name, value in source.items():
            self.register_attr(
                name,
                functools.partial(parse_element, value)
            )


class PathConfig(BaseConfig):
    def __init__(self, path=None, default=None):
        self.bad_names |= {
            'gen_resources',
            'load_entries',
        }

        if path is None and default is None:
            self.load_entries(PathName.CONFIG.value, default=False)
            self.load_entries(PathName.DEFAULT.value, default=True)

        else:
            self.load_entries(path, default)

    @staticmethod
    def gen_resources(path):
        for entry in pkg_resources.resource_listdir(__name__, path):
            full_entry = SEP.join([path, entry])

            if pkg_resources.resource_isdir(__name__, full_entry):
                yield True, entry, full_entry

            else:
                config_name, sep, ext = entry.rpartition('.')

                if ext is not None and ext.casefold() == FileExt.YAML.value:
                    yield False, config_name, full_entry

    def load_entries(self, path, default):
        for is_dir, entry, full_entry in self.gen_resources(path):
            if default:
                base = PathName.DEFAULT
                load_args = [
                    full_entry[len(base.value) + 1:],
                    __name__
                ]
                load_kwargs = {
                    'default_path': path[len(base.value) + 1:]
                }
            else:
                base = PathName.CONFIG
                load_args = [
                    full_entry,
                    __name__
                ]
                load_kwargs = {}

            if is_dir:
                self.register_attr(
                    entry,
                    functools.partial(
                        lambda f, d: PathConfig(f, d), full_entry, default
                    ),
                    'Config Sub-Path: {name}'.format(
                        name=full_entry[len(base.value) + 1:]
                    )
                )
            else:
                self.register_attr(
                    entry,
                    functools.partial(yaml_read, *load_args, **load_kwargs),
                    'YAML Config: {name}'.format(
                        name=full_entry[
                            len(base.value) + 1:
                        ]
                    )
                )


class MainConfig(PathConfig):
    def __init__(self):
        super().__init__()

        self.register_attr(
            'Base',
            lambda: BaseConfig,
            BaseConfig.__doc__
        )

        self.register_attr(
            'to_config',
            lambda: parse_element,
            parse_element.__doc__
        )

        self.register_attr(
            'yaml_read',
            lambda: yaml_read,
            yaml_read.__doc__
        )

        self.register_attr(
            'yaml_write',
            lambda: yaml_write,
            yaml_write.__doc__
        )
