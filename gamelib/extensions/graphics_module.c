#define METH_BOTH METH_VARARGS | METH_KEYWORDS

#include "window_object.h"
#include "buffer_object.h"
#include <structmember.h>


// TODO: Module level docs
PyDoc_STRVAR(Module_doc, "");

static PyObject*
Module_init(PyObject* self)
{
    glfwSetErrorCallback((GLFWerrorfun)glfw_error_callback);
    if (!glfwInit())
        return NULL;
    Py_RETURN_NONE;
}
PyDoc_STRVAR(Module_init_doc,
"Initializes GLFW internally.\n\
This must be called prior to creating windows manually.\n");



static PyMethodDef OpenGLBuffer_methods[] = {
    { "write", (PyCFunction)OpenGLBuffer_write, METH_VARARGS, OpenGLBuffer_write_doc },
    { "read", (PyCFunction)OpenGLBuffer_read, METH_NOARGS, OpenGLBuffer_read_doc },
    { "release", (PyCFunction)OpenGLBuffer_release, METH_NOARGS, OpenGLBuffer_release_doc },
    { NULL }
};

static PyTypeObject OpenGLBufferType = {
    PyObject_HEAD_INIT(NULL)
    .tp_name = "_graphics.OpenGLBuffer",
    .tp_doc = OpenGLBufferType_doc,
    .tp_basicsize = sizeof(OpenGLBuffer),
    .tp_itemsize = 0,
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_new = OpenGLBuffer_new,
    .tp_dealloc = (destructor)OpenGLBuffer_dealloc,
    .tp_methods = OpenGLBuffer_methods,
};



static PyMethodDef Window_methods[] = {
    { "size", (PyCFunction)Window_size, METH_NOARGS, Window_size_doc },
    { "clear", (PyCFunction)Window_clear, METH_BOTH, Window_clear_doc },
    { "swap", (PyCFunction)Window_swap, METH_NOARGS, Window_swap_doc },
    { "destroy", (PyCFunction)Window_destroy, METH_NOARGS, Window_destroy_doc },
    { "poll", (PyCFunction)Window_poll, METH_NOARGS, Window_poll_doc },
    { "destroy_all", (PyCFunction)Window_destroy_all, METH_NOARGS | METH_CLASS, Window_destroy_all_doc },
    { NULL }
};

static PyMemberDef Window_members[] = {
    { "event_list", T_OBJECT_EX, offsetof(Window, event_list), 0,
       "events polled by window framework" },
    { NULL }
};

static PyTypeObject WindowType = {
    PyObject_HEAD_INIT(NULL)
    .tp_name = "_graphics.Window",
    .tp_doc = WindowType_doc,
    .tp_basicsize = sizeof(Window),
    .tp_itemsize = 0,
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_new = Window_new,
    .tp_dealloc = (destructor)Window_dealloc,
    .tp_methods = Window_methods,
    .tp_members = Window_members
};

static PyMethodDef Module_methods[] = {
    { "init", (PyCFunction)Module_init, METH_NOARGS, Module_init_doc },
    { NULL }
};

static PyModuleDef ModuleDef = {
    PyModuleDef_HEAD_INIT,
    .m_name = "_graphics",
    .m_doc = Module_doc,
    .m_size = -1,
    .m_methods = Module_methods,
};

PyMODINIT_FUNC 
PyInit__graphics(void)
{
    PyObject* module = NULL;
    module = PyModule_Create(&ModuleDef);

    WindowError = PyErr_NewException("_graphics.WindowError", NULL, NULL);
    Py_XINCREF(WindowError);
    BufferError = PyErr_NewException("_graphics.BufferError", NULL, NULL);
    Py_XINCREF(BufferError);

    if (module == NULL)
        goto error;


    if (PyModule_AddObject(module, "WindowError", WindowError) < 0)
        goto error;
    if (PyModule_AddObject(module, "BufferError", BufferError) < 0)
        goto error;


    if (PyType_Ready(&WindowType) < 0)
        goto error;
    if (PyType_Ready(&OpenGLBufferType) < 0)
        goto error;


    Py_INCREF(&WindowType);
    if (PyModule_AddObject(module, "Window", (PyObject*)&WindowType) < 0) {
        Py_DECREF(&WindowType);
        goto error;
    }
    Py_INCREF(&OpenGLBufferType);
    if (PyModule_AddObject(module, "OpenGLBuffer", (PyObject*)&OpenGLBufferType) < 0) {
        Py_DECREF(&OpenGLBufferType);
        goto error;
    }

    return module;

error:
    Py_XDECREF(WindowError);
    Py_XDECREF(BufferError);
    Py_XDECREF(module);
    return NULL;
}
