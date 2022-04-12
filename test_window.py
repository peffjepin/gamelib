#!/usr/bin/env python3

import window
import time

window.init()
w = window.Window(100, 100, "hello")

ts = time.time()
frames = 0
while True:
    dt = time.time() - ts
    if dt > 5:
        break

    k = 1 - (dt / 5)
    w.clear(k, k, k, k)
    w.swap()
    frames += 1
    w.poll()

print(f"{frames=} ({frames/5:.2f} fps)")
w.destroy()
