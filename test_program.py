#!/usr/bin/env python3

import _graphics as gfx
gfx.init()
w = gfx.Window(1, 1, "hello", headless=True)

vert = """
#version 330
void main () {
    ;
}
"""
frag = """
#version 330
void main () {
    ;
}
"""

p = gfx.OpenGLProgram(vert=vert, frag=frag)
exit(0)
