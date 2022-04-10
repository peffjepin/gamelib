import sys
import setuptools

is_posix = sys.platform.lower() == "posix"

flags = []
links = []
libraries = ["glfw"]

if is_posix:
    flags.extend(("-std=c11", "-Wall", "-Wpedantic"))

window_module = setuptools.Extension(
    "window",
    sources=[
        "gamelib/extensions/window_module.c",
        "gamelib/extensions/glad.c"
    ],
    libraries=libraries,
    extra_compile_args=flags,
    extra_link_args=links,
)


if __name__ == "__main__":
    setuptools.setup(ext_modules=[window_module])
