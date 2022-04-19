#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <glad.h>
#include "buffer_object.h"
#include "opengl.h"


PyObject *BufferError;


PyObject *OpenGLBuffer_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    PyObject *rv = NULL;
    OpenGLBuffer *self = NULL;
    void *data = NULL;

    char *kwlist[] = {"size", "data", "type", NULL};
    int size = 0;
    PyObject *data_source;
    unsigned int buffer_type = GL_DYNAMIC_DRAW;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|iOI", kwlist,
                                     &size, &data_source, &buffer_type))
        goto cleanup;

    if ((size == 0) == (data_source == Py_None)) {
        // TODO; this should be inproved later, might want to init with large
        // size and only partially fill the buffer
        PyErr_SetString(BufferError, "Either size or data must be given.");
        goto cleanup;
    }

    self = (OpenGLBuffer *) type->tp_alloc(type, 0);
    if (self == NULL)
        goto cleanup;

    Py_buffer bytes_buffer;
    if (data_source != Py_None) {
		if (PyObject_GetBuffer(data_source, &bytes_buffer, PyBUF_SIMPLE) < 0)
            goto cleanup;
        size = bytes_buffer.len;
        data = bytes_buffer.buf;
    }

    unsigned int glo;
    if ((glo = opengl_create_buffer(size, data)) < 0) {
        PyErr_SetString(BufferError, opengl_get_error());
        goto cleanup;
    }

    self->glo = glo;
    self->internal_size = size;
    self->occupied_size = (data == NULL) ? 0 : size;
    rv = (PyObject *)self;

cleanup:
    if (data != NULL)
        PyBuffer_Release(&bytes_buffer);
    if (rv == NULL)
        Py_XDECREF(self);
    return rv;
}


PyObject *OpenGLBuffer_write(OpenGLBuffer *self, PyObject *args)
{
    Py_buffer data_source;
    size_t size = 0;

    if (!PyArg_ParseTuple(args, "y*", &data_source))
        return NULL;
    size = data_source.len;

    /* might need to reallocate the internal opengl buffer if the 
     * size of the given data extends beyond the capacity of the buffer
     */
    if (size > self->internal_size) {
        opengl_release_buffer(self->glo);
        if ((self->glo = opengl_create_buffer(size, data_source.buf)) < 0) {
            PyErr_SetString(BufferError, opengl_get_error());
            PyBuffer_Release(&data_source);
            return NULL;
        }
    }
    else if (opengl_write_buffer(self->glo, 0, data_source.len, data_source.buf) < 0) {
        PyErr_SetString(BufferError, opengl_get_error());
        PyBuffer_Release(&data_source);
        return NULL;
    }
    self->occupied_size = size;
    Py_RETURN_NONE;
}


PyObject *OpenGLBuffer_read(OpenGLBuffer *self)
{
    char data[self->occupied_size];
    int read_ok = opengl_read_buffer(self->glo, 0, self->occupied_size, data);

    if (read_ok < 0) {
        PyErr_SetString(BufferError, opengl_get_error());
        return NULL;
    }
    
    return PyBytes_FromStringAndSize((const char *)data, self->occupied_size);
}


PyObject *OpenGLBuffer_release(OpenGLBuffer *self)
{
    opengl_release_buffer(self->glo);
    Py_RETURN_NONE;
}


void OpenGLBuffer_dealloc(OpenGLBuffer *self)
{
    OpenGLBuffer_release(self);
    Py_TYPE(self)->tp_free(self);
}
