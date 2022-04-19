#define MAX_WINDOWS 8
#include "window_object.h"
#include "opengl.h"

static Window* active_window;
static Window* WINDOWS[MAX_WINDOWS];
static int register_window(Window *);
static void unregister_window(Window *);
static void activate_window(Window *);
static void glfw_key_callback(GLFWwindow *glfw, int key, int scancode, int action, int mods);


PyObject* WindowError;


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
    opengl_initialize();
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
Window_destroy_all(PyObject *self)
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


void
glfw_error_callback(int code, char *message)
{
    PyErr_SetString(WindowError, message);
}


static void 
activate_window(Window *window)
{
    if (active_window != window) {
        active_window = window;
        glfwMakeContextCurrent(window->_glfw);
    }
}
