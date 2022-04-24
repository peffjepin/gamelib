#!/usr/bin/env python3

import time
import _graphics as gfx

gfx.init()

w1 = gfx.Window(400, 300, "hello1")
w2 = gfx.Window(300, 400, "hello2")

ts = time.time()
frames = 0
while True:
    dt = time.time() - ts
    if dt > 5:
        break

    k = 1 - (dt / 5)
    ik = 1 - k

    w1.clear(k, k, k, k)
    w1.swap()
    w2.clear(ik, ik, ik, ik)
    w2.swap()
    frames += 1
    w1.poll()
    w2.poll()

print(f"{frames=} ({frames/5:.2f} fps)")
gfx.Window.destroy_all()
exit(0)
