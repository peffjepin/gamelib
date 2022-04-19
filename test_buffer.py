#!/usr/bin/env python3

import _graphics as gfx
import numpy as np

gfx.init()
w = gfx.Window(100, 100, "hello")

d1 = np.arange(10)
buf = gfx.OpenGLBuffer(data=d1.tobytes())
print(np.frombuffer(buf.read(), int))

d2 = np.arange(5) * 2
buf.write(d2.tobytes())
print(np.frombuffer(buf.read(), int))

buferr = gfx.OpenGLBuffer(size=100, data=d2)
