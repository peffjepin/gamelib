#!/usr/bin/env python3

import _graphics as gfx
import numpy as np

gfx.init()
w = gfx.Window(100, 100, "hello")

# buffer should work
d1 = np.arange(10)
buf = gfx.OpenGLBuffer(data=d1.tobytes())
print(np.frombuffer(buf.read(), int))

# buffer should read back only occupied space
d2 = np.arange(5) * 2
buf.write(d2.tobytes())
print(np.frombuffer(buf.read(), int))

# buffer should grow
d3 = np.arange(15) * 3
buf.write(d3.tobytes())
print(np.frombuffer(buf.read(), int))

# buffer should error
buf_err = gfx.OpenGLBuffer(size=100, data=d2)
