"""The resources module is responsible for serving the rest of the library
paths to files.

Manage searching with:
    set_content_roots
    add_content_roots
    add_supported_extensions

Find discovered files with:
    # for any file, must provide extension
    get_file

    # shortcuts for specific filetypes, don't specify extension
    get_image_file
    get_model_file
    get_shader_files
"""

import pathlib
import collections


_resource_roots = []
_resource_cache = collections.defaultdict(list)
_shader_extensions = (".vert", ".frag", ".tesc", ".tese", ".geom", ".glsl")
_image_extensions = (".jpg", ".png")
_3d_model_extensions = (".obj",)
_supported_extensions = [
    *_shader_extensions,
    *_image_extensions,
    *_3d_model_extensions,
]


def clear_cache():
    """Clear all cached resources that have been discovered."""

    _resource_cache.clear()


def set_content_roots(*dirs):
    """Sets the root directories that will be searched to find resources.
    Calling this will clear all previously cached resources.

    Parameters
    ----------
    *dirs : pathlib.Path
    """

    _resource_roots.clear()
    _resource_roots.extend(dirs)
    _resource_cache.clear()
    for path in dirs:
        _search_directory(path)


def add_content_roots(*dirs):
    """Similar to `set_content_roots` but doesn't overwrite what's currently
    set, and doesn't clear the cache.

    Parameters
    ----------
    *dirs : pathlib.Path
    """

    _resource_roots.extend(dirs)
    for path in dirs:
        _search_directory(path)


def add_supported_extensions(*extensions):
    """Tell the resources module to look for this filetype.

    Parameters
    ----------
    *extensions : str
    """

    cleaned = []
    for ext in extensions:
        if ext[0] != ".":
            cleaned.append(f".{ext}")
        else:
            cleaned.append(ext)

    _supported_extensions.extend(cleaned)
    for path in _resource_roots:
        _search_directory(path, exts=cleaned)


def get_file(filename):
    """Tries to get a path to the requested filename.

    Parameters
    ----------
    filename : str
        This should include the file's extension. A parent directory can be
        specified for ambiguous files: assets1/water.png, assets2/water.png

    Returns
    -------
    pathlib.Path

    Raises
    ------
    KeyError:
        When the file cannot be located.
    """

    if "/" in filename:
        dir_, name = filename.split("/")
    elif "\\" in filename:
        dir_, name = filename.split("\\")
    else:
        dir_, name = None, filename

    if dir_ is None:
        paths = _resource_cache[name]
        if paths:
            return paths[0]

    for path in _resource_cache[name]:
        if path.parent.name == dir_:
            return path

    raise KeyError(f"Unable to locate {filename=}.")


def get_shader_files(name):
    """Tries to get a list of paths to shader source files with
    the given name.

    Parameters
    ----------
    name : str
        for shader made up of files water.vert, water.frag
        name would be "water"

    Returns
    -------
    list[pathlib.Path]

    Raises
    ------
    KeyError:
        When the files could not be found for given name.
    """

    sources = []
    for ext in _shader_extensions:
        try:
            if name.endswith(ext):
                return get_file(name)
            sources.append(get_file(name + ext))
        except KeyError:
            pass

    if not sources:
        raise KeyError(f"Couldn't locate {name=}.")

    return sources


def get_image_file(name):
    """Tries to get the path to an image file with the given name.

    Parameters
    ----------
    name : str

    Returns
    -------
    pathlib.Path

    Raises
    ------
    KeyError:
        When the file could not be found.
    """

    for ext in _image_extensions:
        try:
            if name.endswith(ext):
                return get_file(name)
            return get_file(name + ext)
        except KeyError:
            pass
    raise KeyError(f"Couldn't locate {name=}.")


def get_model_file(name):
    """Tries to get the path to a cached 3d model file.

    Parameters
    ----------
    name : str

    Returns
    -------
    pathlib.Path

    Raises
    ------
    KeyError:
        When the file can't be located.
    """

    for ext in _3d_model_extensions:
        try:
            if name.endswith(ext):
                return get_file(name)
            return get_file(name + ext)
        except KeyError:
            pass
    raise KeyError(f"Couldn't locate {name=}.")


def _search_directory(path, exts=_supported_extensions):
    """Search through the given directory path recursively and cache files
    found with supported extensions."""

    assert path.is_dir()

    for path in path.iterdir():
        if path.is_dir():
            _search_directory(path)
        elif any(path.name.endswith(ext) for ext in exts):
            _resource_cache[path.name].append(path)