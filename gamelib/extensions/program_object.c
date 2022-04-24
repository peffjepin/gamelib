#include <glad.h>
#include "program_object.h"
#include "opengl.h"


PyObject *GLSLError;


PyObject *
OpenGLProgram_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    PyObject *rv = NULL;
    OpenGLProgram *self = NULL;

    int vert_id=-1, tesc_id=-1, tese_id=-1, geom_id=-1, frag_id=-1;
    char *vert=NULL, *tesc=NULL, *tese=NULL, *geom=NULL, *frag=NULL;
    char *kwlist[] = {"vert", "tesc", "tese", "geom", "frag", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "z|zzzz", kwlist,
                                     &vert, &tesc, &tese, &geom, &frag))
        goto cleanup;

    self = (OpenGLProgram *) type->tp_alloc(type, 0);
    if (self == NULL)
        goto cleanup;

    if (vert == NULL) {
        PyErr_SetString(GLSLError, "A vertex shader stage must be given");
        goto cleanup;
    }

    /* Compile all given shader stages, checking for errors along the way
     */
    self->nshaders = 0;

    vert_id = opengl_create_shader_stage(GL_VERTEX_SHADER, vert);
    self->shader_ids[self->nshaders] = vert_id;
    self->nshaders++;
    if (vert_id < 0) {
        OPENGL_CONSUME_ERROR(error);
        PyErr_SetString(GLSLError, error);
        goto cleanup;
    }

    if (tesc != NULL) {
        tesc_id = opengl_create_shader_stage(GL_TESS_CONTROL_SHADER, tesc);
        self->shader_ids[self->nshaders] = tesc_id;
        self->nshaders++;
        if (tesc_id < 0) {
            OPENGL_CONSUME_ERROR(error);
            PyErr_SetString(GLSLError, error);
            goto cleanup;
        }
    }

    if (tese != NULL) {
        tese_id = opengl_create_shader_stage(GL_TESS_EVALUATION_SHADER, tese);
        self->shader_ids[self->nshaders] = tese_id;
        self->nshaders++;
        if (tese_id < 0) {
            OPENGL_CONSUME_ERROR(error);
            PyErr_SetString(GLSLError, error);
            goto cleanup;
        }
    }

    if (geom != NULL) {
        geom_id = opengl_create_shader_stage(GL_GEOMETRY_SHADER, geom);
        self->shader_ids[self->nshaders] = geom_id;
        self->nshaders++;
        if (geom_id < 0) {
            OPENGL_CONSUME_ERROR(error);
            PyErr_SetString(GLSLError, error);
            goto cleanup;
        }
    }

    if (frag != NULL) {
        frag_id = opengl_create_shader_stage(GL_FRAGMENT_SHADER, frag);
        self->shader_ids[self->nshaders] = frag_id;
        self->nshaders++;
        if (frag_id < 0) {
            OPENGL_CONSUME_ERROR(error);
            PyErr_SetString(GLSLError, error);
            goto cleanup;
        }
    }

    int program_id = opengl_create_program(self->shader_ids, self->nshaders);
    if (program_id < 0) {
        OPENGL_CONSUME_ERROR(error);
        PyErr_SetString(GLSLError, error);
        goto cleanup;
    }

    self->id = program_id;
    rv = (PyObject *)self;

cleanup:
    if (rv == NULL) {
        Py_XDECREF(self);

        /* if we are in a failure state make sure to delete any shaders
         * which were successfully compiled before the error was raised
         */
        if (self != NULL) {
            for (int i=0; i<self->nshaders; i++)
                opengl_release_shader(self->shader_ids[i]);
        }
    }

    return rv;
}

void 
OpenGLProgram_dealloc(OpenGLProgram *self)
{
    for (unsigned int i=0; i < self->nshaders; i++) {
        unsigned int shader_id = self->shader_ids[i];
        opengl_release_shader(shader_id);
    }

    opengl_release_program(self->id);
    Py_TYPE(self)->tp_free(self);
}
