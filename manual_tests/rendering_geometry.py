import numpy as np

import gamelib
from gamelib.geometry import Cube
from gamelib.transforms import Mat4, Transform
from gamelib.rendering import PerspectiveCamera
from gamelib.rendering import ShaderProgram
from gamelib.input import InputSchema


gamelib.init()
ctx = gamelib.get_context()
ctx.enable(ctx.DEPTH_TEST)


camera = PerspectiveCamera(
    pos=(0, -2, 0),
    dir=(0, 1, 0),
    controller=True
)
cube = Cube()
transform = Transform(
    scale=(5, 1, 1),
    pos=(0, 0, 0),
    axis=(0, 0, 1),
    theta=0
)
model_matrix = np.identity(4, "f4")
shader = ShaderProgram(
    "flat_shaded",
    buffers={"v_pos": cube.vertices},
    uniforms={
        "proj": camera.projection_matrix,
        "view": camera.view_matrix,
        "model": model_matrix
    },
    index_buffer=cube.indices
)

waiting_for_input = False

def next_test():
    global waiting_for_input
    waiting_for_input = False


def quit():
    global waiting_for_input
    waiting_for_input = False
    gamelib.exit()

schema = InputSchema(
    ("y", "down", next_test),
    ("n", "down", quit)
)

def prompt(msg):
    global waiting_for_input
    print(msg)
    print("Continue? y/n")
    print("")
    waiting_for_input = True
    

prompt("Rotating right.")
theta = 0
while waiting_for_input:
    gamelib.clear()
    theta += 1
    model_matrix[:] = Mat4.rotate_about_z(theta)
    shader.render()
    gamelib.update()


prompt("Rotating left.")
theta = 0
while waiting_for_input:
    gamelib.clear()
    theta -= 1
    model_matrix[:] = Mat4.rotate_about_z(theta)
    shader.render()
    gamelib.update()


prompt("Rotating right.")
theta = 0
while waiting_for_input:
    gamelib.clear()
    theta += 1
    model_matrix[:] = Mat4.rotate_about_y(theta)
    shader.render()
    gamelib.update()


prompt("Rotating left.")
theta = 0
while waiting_for_input:
    gamelib.clear()
    theta -= 1
    model_matrix[:] = Mat4.rotate_about_y(theta)
    shader.render()
    gamelib.update()


prompt("Rotating down.")
theta = 0
while waiting_for_input:
    gamelib.clear()
    theta += 1
    model_matrix[:] = Mat4.rotate_about_x(theta)
    shader.render()
    gamelib.update()


prompt("Rotating up.")
theta = 0
while waiting_for_input:
    gamelib.clear()
    theta -= 1
    model_matrix[:] = Mat4.rotate_about_x(theta)
    shader.render()
    gamelib.update()
    

camera.pos = (-2, -2, -2)
camera.direction = (2, 2, 2)


prompt("Rotating right.")
theta = 0
while waiting_for_input:
    gamelib.clear()
    theta += 1
    model_matrix[:] = Mat4.rotate_about_axis(camera.direction, theta)
    shader.render()
    gamelib.update()


prompt("Rotating left.")
theta = 0
while waiting_for_input:
    gamelib.clear()
    theta -= 1
    model_matrix[:] = Mat4.rotate_about_axis(camera.direction, theta)
    shader.render()
    gamelib.update()


camera.pos = (0, -2, 0)
camera.direction = (0, 1, 0)


prompt("Stretching horizontally.")
scale = 1
while waiting_for_input:
    gamelib.clear()
    scale += 0.02
    model_matrix[:] = Mat4.scale((scale, 1, 1))
    shader.render()
    gamelib.update()


prompt("Stretching vertically.")
scale = 1
while waiting_for_input:
    gamelib.clear()
    scale += 0.02
    model_matrix[:] = Mat4.scale((1, 1, scale))
    shader.render()
    gamelib.update()


camera.pos = (0, 0, 2)
camera.direction = (0, 0, -1)
camera.up = (0, 1, 0)


prompt("Stretching vertically.")
scale = 1
while waiting_for_input:
    gamelib.clear()
    scale += 0.02
    model_matrix[:] = Mat4.scale((1, scale, 1))
    shader.render()
    gamelib.update()


camera.pos = (0, -10, 0)
camera.direction = (0, 1, 0)
camera.up = (0, 0, 1)


prompt("Moving left.")
offset = 0
while waiting_for_input:
    gamelib.clear()
    offset += 0.02
    model_matrix[:] = Mat4.translation((-offset, 0, 0))
    shader.render()
    gamelib.update()


prompt("Moving right.")
offset = 0
while waiting_for_input:
    gamelib.clear()
    offset += 0.02
    model_matrix[:] = Mat4.translation((offset, 0, 0))
    shader.render()
    gamelib.update()


prompt("Moving up.")
offset = 0
while waiting_for_input:
    gamelib.clear()
    offset += 0.02
    model_matrix[:] = Mat4.translation((0, 0, offset))
    shader.render()
    gamelib.update()


prompt("Moving down.")
offset = 0
while waiting_for_input:
    gamelib.clear()
    offset += 0.02
    model_matrix[:] = Mat4.translation((0, 0, -offset))
    shader.render()
    gamelib.update()


camera.pos = (0, 0, 10)
camera.direction = (0, 0, -1)
camera.up = (0, 1, 0)


prompt("Moving up.")
offset = 0
while waiting_for_input:
    gamelib.clear()
    offset += 0.02
    model_matrix[:] = Mat4.translation((0, offset, 0))
    shader.render()
    gamelib.update()


prompt("Moving down.")
offset = 0
while waiting_for_input:
    gamelib.clear()
    offset += 0.02
    model_matrix[:] = Mat4.translation((0, -offset, 0))
    shader.render()
    gamelib.update()


camera.pos = (0, -5, 0)
camera.direction = (0, 1, 0)
camera.up = (0, 0, 1)


prompt("Cycle up/down, cycle width, rotate right.")
i = 0
while waiting_for_input:
    gamelib.clear()
    sin = np.sin(i/66)
    t = Transform(
        pos=(0, 0, sin),
        scale=(1.5 + sin, 1, 1),
        axis=(0, 0, 1),
        theta=i,
    )
    model_matrix[:] = t.matrix
    shader.render()
    gamelib.update()
    i += 1


gamelib.exit()

