#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <GLFW/glfw3.h>


static PyObject *WindowError;
static GLFWwindow *window = NULL;


static void key_callback(GLFWwindow *win, int key, int scancode, int action, int mods)
{
    printf("key: %c, scancode: %d, action: %d, mods: %d\n", key, scancode, action, mods);
}


static void error_callback(int code, char *message)
{
    PyErr_SetString(WindowError, message);
}


static PyObject * 
window_create(PyObject* self, PyObject* args)
{
    int width, height;
    char *title;

    if (!PyArg_ParseTuple(args, "iis", &width, &height, &title))
        return NULL;

    glfwSetErrorCallback((GLFWerrorfun) error_callback);
    if (!glfwInit())
        return NULL;

    // glfwWindowHint(GLFW_VISIBLE, GLFW_FALSE);
    window = glfwCreateWindow(width, height, title, NULL, NULL);
    if (!window)
    {
        glfwTerminate();
        return NULL;
    }

    glfwMakeContextCurrent(window);
    glfwSetKeyCallback(window, key_callback);

    Py_RETURN_NONE;
}


static PyObject * 
window_clear(PyObject* self, PyObject* args)
{
    float r, g, b, a;

    if (!PyArg_ParseTuple(args, "ffff", &r, &g, &b, &a))
        return NULL;

    glClearColor(r, g, b, a);
    glClear(GL_COLOR_BUFFER_BIT);

    Py_RETURN_NONE;
}


static PyObject * 
window_swap(PyObject* self, PyObject* args)
{
    glfwSwapBuffers(window);

    Py_RETURN_NONE;
}


static PyObject * 
window_poll(PyObject* self, PyObject* args)
{
    glfwPollEvents();

    Py_RETURN_NONE;
}


static PyObject * 
window_destroy(PyObject* self, PyObject* args)
{
    glfwTerminate();

    Py_RETURN_NONE;
}


static PyMethodDef window_module_functions[] = {
    {"create", window_create, METH_VARARGS, "initialize the window"},
    {"clear", window_clear, METH_VARARGS, "clear the framebuffer"},
    {"swap", window_swap, METH_VARARGS, "swap framebuffers"},
    {"poll", window_poll, METH_VARARGS, "poll for input events"},
    {"destroy", window_destroy, METH_VARARGS, "close the window"},
    {NULL, NULL, 0, NULL}
};


static struct PyModuleDef window_module = {
    PyModuleDef_HEAD_INIT,
    "window",  
    NULL,    
    -1,      
    window_module_functions 
};


PyMODINIT_FUNC PyInit_window(void)
{
    PyObject *module;

    module = PyModule_Create(&window_module);
    if (module == NULL)
        return NULL;

    WindowError = PyErr_NewException("window.WindowError", NULL, NULL);
    Py_XINCREF(WindowError);
    if (PyModule_AddObject(module, "WindowError", WindowError) < 0)
    {
        Py_XDECREF(WindowError);
        Py_CLEAR(WindowError);
        Py_DECREF(module);
        return NULL;
    }

    return module;
}
