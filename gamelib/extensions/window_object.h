#ifndef GAMELIB_WINDOW_OBJECT_H
#define GAMELIB_WINDOW_OBJECT_H

#define GLFW_INCLUDE_NONE
#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <glad.h>
#include <glfw3.h>


void glfw_error_callback(int code, char *message);

typedef struct {
    PyObject_HEAD
    PyObject *event_list;
    int width;
    int height;
    char *title;
    GLFWwindow *_glfw;
} Window;


extern PyObject *WindowError;


PyObject *Window_size(Window *self);
PyDoc_STRVAR(Window_size_doc,
"Get's the window's size (width, height) in px.\n\
\n\
Returns\n\
-------\n\
tuple\n");

PyObject *Window_clear(Window *self, PyObject *args, PyObject *kwds);
PyDoc_STRVAR(Window_clear_doc,
"Issues an OpenGL clear command with the given colors.\n\
Params expected in range 0-1\n\
\n\
Parameters\n\
----------\n\
r : float = 0.0\n\
g : float = 0.0\n\
b : float = 0.0\n\
a : float = 0.0\n");

PyObject *Window_swap(Window *self);
PyDoc_STRVAR(Window_swap_doc, "Swap the windows framebuffers.");

PyObject *Window_destroy(Window *self);
PyDoc_STRVAR(Window_destroy_doc, "Destroys the window.");

PyObject *Window_poll(Window *self);
// TODO: expand docs to explain how this mechanism works once fleshed out
// Note: this method can be pulled off the Window class to the module level
PyDoc_STRVAR(Window_poll_doc, "Poll glfw framework for events");

void Window_dealloc(Window *self);
PyDoc_STRVAR(WindowType_doc,
"A GLFW Window.\n\
\n\
Create a new window with the glfw framework:\n\
\n\
Parameters\n\
----------\n\
width      : int (px)\n\
height     : int (px)\n\
title      : str\n\
headless   : bool=False\n\
resizeable : bool=True\n");
PyObject *Window_new(PyTypeObject *type, PyObject *args, PyObject *kwds);

PyObject *Window_destroy_all(PyObject *self);
PyDoc_STRVAR(Window_destroy_all_doc,
"Terminates GLFW internally.\n\
This will destroy all running windows.\n");

#endif // GAMELIB_WINDOW_OBJECT_H
