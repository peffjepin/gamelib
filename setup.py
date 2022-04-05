import sys
import setuptools
import subprocess
import shlex

is_posix = sys.platform.lower() == "posix"


class PkgConfig:
    # namespace for pkg-config cli
    @staticmethod
    def _cmd(options, packages):
        cmd = shlex.split(
            f"pkg-config {' '.join(options)} {' '.join(packages)}"
        )
        p = subprocess.run(cmd, check=True, capture_output=True)
        return p.stdout.decode("utf-8").rstrip()

    @classmethod
    def configure_extension(cls, extension, packages, options=()):
        cflags_options = (*options, "--cflags")
        libs_options = (*options, "--libs")

        cflags = cls._cmd(cflags_options, packages).split()
        libs = cls._cmd(libs_options, packages).split()

        extension.extra_compile_args.extend(cflags)
        extension.extra_link_args.extend(libs)


flags = ["-std=c11", "-Wall"]
if is_posix:
    flags.append("-Wpedantic")

window_module = setuptools.Extension(
    "window",
    sources=["gamelib/extensions/window_module.c"],
    extra_compile_args=flags,
    extra_link_args=["-lglfw", "-lGL"]
)


if __name__ == "__main__":
    setuptools.setup(ext_modules=[window_module])
