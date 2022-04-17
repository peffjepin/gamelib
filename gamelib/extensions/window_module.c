#define MAX_WINDOWS 8
#define METH_BOTH METH_VARARGS | METH_KEYWORDS

#include "window.h"
#include <structmember.h>


static Window* active_window;
static Window* WINDOWS[MAX_WINDOWS];
static int register_window(Window *);
static void unregister_window(Window *);
static void activate_window(Window *);

static void glfw_key_callback(GLFWwindow *glfw, int key, int scancode, int action, int mods);
static void glfw_error_callback(int code, char *message);


PyObject *
Window_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    char *kwlist[] = {"width", "height", "title", "headless", "resizeable", NULL};
    int width, height, headless = 0, resizable = 1;
    char *title;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "iis|pp", kwlist,
                                     &width, &height, &title,
                                     &headless, &resizable))
        return NULL;

    Window *self = (Window *) type->tp_alloc(type, 0);
    if (self == NULL)
        return NULL;

    if (headless)
        glfwWindowHint(GLFW_VISIBLE, GLFW_FALSE);

    if (!resizable)
        glfwWindowHint(GLFW_RESIZABLE, GLFW_FALSE);

    GLFWwindow *window = glfwCreateWindow(width, height, title, NULL, NULL);
    if (!window) {
        if (!PyErr_Occurred())
            PyErr_SetString(
                WindowError,
                "You must initialize glfw before creating a window."
            );
        return NULL;
    }

    PyObject *event_list = PyList_New(0);
    if (!event_list)
        return NULL;

    self->event_list = event_list;
    self->width = width;
    self->height = height;
    self->title = title;
    self->_glfw = window;

    if (register_window(self) < 0) {
        PyErr_SetString(WindowError, "Exceeded maximum window count");
        return NULL;
    }

    glfwMakeContextCurrent(window);
    gladLoadGL();
    glfwSetKeyCallback(window, glfw_key_callback);

    if (active_window != NULL) {
        glfwMakeContextCurrent(active_window->_glfw);
    }

    return (PyObject *) self;
}


PyObject *
Window_size(Window *self)
{
    glfwGetWindowSize(self->_glfw, &self->width, &self->height);
    return Py_BuildValue("(ii)", self->width, self->height);
}


PyObject *
Window_clear(Window *self, PyObject *args, PyObject *kwds)
{
    activate_window(self);

    char *kwlist[] = {"r", "g", "b", "a", NULL};

    float r = 0.0, g = 0.0, b = 0.0, a = 0.0;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|ffff", kwlist,
                                     &r, &g, &b, &a))
        return NULL;

    glClearColor(r, g, b, a);
    glClear(GL_COLOR_BUFFER_BIT);

    Py_RETURN_NONE;
}


PyObject *
Window_swap(Window *self)
{
    glfwSwapBuffers(self->_glfw);
    Py_RETURN_NONE;
}


PyObject *
Window_destroy(Window *self)
{
    unregister_window(self);
    if (self->_glfw != NULL) {
        glfwDestroyWindow(self->_glfw);
        self->_glfw = NULL;
    }
    Py_RETURN_NONE;
}


PyObject *
Window_poll(Window *self)
{
    glfwPollEvents();
    Py_RETURN_NONE;
}


void
Window_dealloc(Window *self)
{
    Window_destroy(self);
    Py_DECREF(self->event_list);
    Py_TYPE(self)->tp_free(self);
}


PyObject *
Module_init(PyObject *self)
{
    glfwSetErrorCallback((GLFWerrorfun) glfw_error_callback);
    if (!glfwInit())
        return NULL;
    Py_RETURN_NONE;
}


PyObject *
Module_destroy_all(PyObject *self)
{
    glfwTerminate();
    Py_RETURN_NONE;
}


/* register a gamelib window so it can be found by glfw
 * returns -1 if there are too many windows, or 0 on success
 */
static int
register_window(Window *window)
{
    int i = 0;
    for (;;i++) {
        if (i >= MAX_WINDOWS)
            return -1;
        if (WINDOWS[i] == NULL)
            break;
    }
    WINDOWS[i] = window;
    return 0;
}


/* unregister a gamelib window before we destroy it
 */
static void
unregister_window(Window *window)
{
    for (int i = 0; i < MAX_WINDOWS; i++) {
        if (WINDOWS[i] == window) {
            WINDOWS[i] = NULL;
            return;
        }
    }
}


/* get a gamelib window associated with a glfw window pointer
 * returns NULL if window is not found
 */
static Window *
get_window_from_glfw(GLFWwindow *glfw)
{
    for (int i = 0; i < MAX_WINDOWS; i++) {
        Window *registered = WINDOWS[i];
        if (registered && registered->_glfw == glfw) {
            return registered;
        }
    }
    return NULL;
}


static void
glfw_key_callback(GLFWwindow *glfw, int key, int scancode, int action, int mods)
{
    if (PyErr_Occurred())
        return;

    PyObject *tuple = Py_BuildValue("(iii)", key, action, mods);
    if (!tuple)
        return;

    if (active_window->_glfw == glfw) {
        PyList_Append(active_window->event_list, tuple);
    }
    else {
        Window *window = get_window_from_glfw(glfw);
        if (!window)
            return;
        PyList_Append(window->event_list, tuple);
    }
}


static void
glfw_error_callback(int code, char *message)
{
    PyErr_SetString(WindowError, message);
}


static void activate_window(Window *window)
{
    if (active_window != window) {
        active_window = window;
        glfwMakeContextCurrent(window->_glfw);
    }
}


static PyMethodDef Window_methods[] = {
    {"size",    (PyCFunction) Window_size,    METH_NOARGS, Window_size_doc},
    {"clear",   (PyCFunction) Window_clear,   METH_BOTH,   Window_clear_doc},
    {"swap",    (PyCFunction) Window_swap,    METH_NOARGS, Window_swap_doc},
    {"destroy", (PyCFunction) Window_destroy, METH_NOARGS, Window_destroy_doc},
    {"poll",    (PyCFunction) Window_poll,    METH_NOARGS, Window_poll_doc},
    {NULL}
};

static PyMemberDef Window_members[] = {
    {"event_list", T_OBJECT_EX, offsetof(Window, event_list), 0,
     "events polled by window framework"},
    {NULL}
};

static PyTypeObject WindowType = {
    PyObject_HEAD_INIT(NULL)
    .tp_name = "window.Window",
    .tp_doc = WindowType_doc,
    .tp_basicsize = sizeof(Window),
    .tp_itemsize = 0,
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_new = Window_new,
    .tp_dealloc = (destructor) Window_dealloc,
    .tp_methods = Window_methods,
    .tp_members = Window_members
};

static PyMethodDef Module_methods[] = {
    {"init",        (PyCFunction) Module_init,        METH_NOARGS, Module_init_doc},
    {"destroy_all", (PyCFunction) Module_destroy_all, METH_NOARGS, Module_destroy_all_doc},
    {NULL}
};

static PyModuleDef ModuleDef = {
    PyModuleDef_HEAD_INIT,
    .m_name = "window",
    .m_doc = Module_doc,
    .m_size = -1,
    .m_methods = Module_methods,
};

PyMODINIT_FUNC PyInit_window(void)
{
    PyObject *module = NULL;
    module = PyModule_Create(&ModuleDef);

    WindowError = PyErr_NewException("window.WindowError", NULL, NULL);
    Py_XINCREF(WindowError);

    if (module == NULL)
        goto error;

    if (PyModule_AddObject(module, "WindowError", WindowError) < 0)
        goto error;

    if (PyType_Ready(&WindowType) < 0)
        goto error;

    Py_INCREF(&WindowType);
    if (PyModule_AddObject(module, "Window", (PyObject *) &WindowType) < 0) {
        Py_DECREF(&WindowType);
        goto error;
    }

    return module;

error:
    Py_XDECREF(WindowError);
    Py_XDECREF(module);
    return NULL;
}
