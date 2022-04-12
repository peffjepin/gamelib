import os
import setuptools


PLATFORM = os.name.lower()
MACOS = "macos"
WINDOWS = "nt"
POSIX = "posix"
COMMON = "common"

glfw_dir = "glfw"
glad_dir = "glad"
cext_dir = "gamelib/extensions"

glfw_source = {
    COMMON: [
        "context.c",
        "init.c",
        "input.c",
        "monitor.c",
        "platform.c",
        "vulkan.c",
        "window.c",
        "egl_context.c",
        "osmesa_context.c",
        "null_init.c",
        "null_monitor.c",
        "null_window.c",
        "null_joystick.c",
    ],
    POSIX: [
        "posix_time.c",
        "posix_module.c",
        "posix_thread.c",
        "linux_joystick.c",
        "x11_init.c",
        "x11_monitor.c",
        "x11_window.c",
        "xkb_unicode.c",
        "glx_context.c",
    ],
    WINDOWS: [
        "win32_module.c",
        "win32_time.c",
        "win32_thread.c",
        "win32_init.c",
        "win32_joystick.c",
        "win32_monitor.c",
        "win32_window.c",
        "wgl_context.c",
    ],
    MACOS: [
        "posix_module.c",
        "posix_thread.c",
        "cocoa_time.c",
        "cocoa_init.m",
        "cocoa_joystick.m",
        "cocoa_monitor.m",
        "cocoa_window.m",
        "nsgl_context.m",
    ],
}

cflags = {
    POSIX: ["-Wall", "-D_GLFW_X11", "-Wno-missing-braces"],
    WINDOWS: ["/Wall", "/D_GLFW_WIN32"],
    MACOS: ["-Wall", "-D_GLFW_COCOA", "-D_GLFW_BUILD_DLL"],  # FIXME
}

libraries = {
    POSIX: ["rt", "m", "dl"],
    WINDOWS: ["gdi32"],
    MACOS: ["Cocoa", "IOKit", "CoreFoundation"],  # FIXME
}

relevant_glfw_source = glfw_source[COMMON] + glfw_source[PLATFORM]
relevant_glfw_files = [f"{glfw_dir}/{fn}" for fn in relevant_glfw_source]

window_module = setuptools.Extension(
    "window",
    sources=[
        *relevant_glfw_files,
        f"{glad_dir}/glad.c",
        f"{cext_dir}/window_module.c",
    ],
    libraries=libraries[PLATFORM],
    include_dirs=[glad_dir, glfw_dir],
    extra_compile_args=cflags[PLATFORM],
)


if __name__ == "__main__":
    setuptools.setup(ext_modules=[window_module])
