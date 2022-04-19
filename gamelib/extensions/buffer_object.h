#ifndef GAMELIB_BUFFER_OBJECT_H
#define GAMELIB_BUFFER_OBJECT_H

#define PY_SSIZE_T_CLEAN
#include <Python.h>

typedef struct {
    PyObject_HEAD
    size_t occupied_size;
    size_t internal_size;
    unsigned int glo; 
} OpenGLBuffer;

extern PyObject *BufferError;

// TODO: write docs later once the graphics module is more fleshed out.

PyObject *OpenGLBuffer_new(PyTypeObject *type, PyObject *args, PyObject *kwds);
PyDoc_STRVAR(OpenGLBufferType_doc, "");

PyObject *OpenGLBuffer_write(OpenGLBuffer *self, PyObject *args);
PyDoc_STRVAR(OpenGLBuffer_write_doc, "");

PyObject *OpenGLBuffer_read(OpenGLBuffer *self);
PyDoc_STRVAR(OpenGLBuffer_read_doc, "");

PyObject *OpenGLBuffer_release(OpenGLBuffer *self);
PyDoc_STRVAR(OpenGLBuffer_release_doc, "");

void OpenGLBuffer_dealloc(OpenGLBuffer *self);


#endif  // GAMELIB_BUFFER_OBJECT_H
