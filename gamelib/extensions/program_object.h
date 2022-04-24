#ifndef GAMELIB_SHADER_OBJECT_H
#define GAMELIB_SHADER_OBJECT_H

#define PY_SSIZE_T_CLEAN
#include <Python.h>

typedef struct {
    PyObject_HEAD
    unsigned int id; 
    unsigned int shader_ids[5];
    size_t nshaders;
} OpenGLProgram;

extern PyObject *GLSLError;

// TODO: write docs later once the graphics module is more fleshed out.

PyObject *OpenGLProgram_new(PyTypeObject *type, PyObject *args, PyObject *kwds);
PyDoc_STRVAR(OpenGLProgramType_doc, "");

void OpenGLProgram_dealloc(OpenGLProgram *self);


#endif  // GAMELIB_SHADER_OBJECT_H
