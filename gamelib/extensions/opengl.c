#include <stdlib.h>
#include <stdbool.h>
#include <string.h>

#include <glad.h>
#include "opengl.h"

static bool initialized = false;

static const char **error_message;
static bool err_occurred = false;

static bool report_possible_error(const char *msg);
static bool check_errors(void);
static void clear_error(void);

void GLAPIENTRY gl_error_callback(GLenum source, GLenum type, GLuint id, 
                                  GLenum severity, GLsizei length, 
                                  const GLchar* message, const void* userParam);


void 
opengl_initialize(void)
{
    if (initialized)
        return;

    GLint major, minor;
    glGetIntegerv(GL_MAJOR_VERSION, &major);
    glGetIntegerv(GL_MINOR_VERSION, &minor);

    if (major > 4 || (major == 4 && minor >= 3)) {
        glEnable(GL_DEBUG_OUTPUT);
        glDebugMessageCallback(gl_error_callback, 0);
    }

    initialized = true;
}


int 
opengl_create_buffer(size_t buffer_size, void *data)
{
    GLuint buffer_glo;
    glGenBuffers(1, &buffer_glo);
    glBindBuffer(GL_ARRAY_BUFFER, buffer_glo);
    glBufferData(GL_ARRAY_BUFFER, buffer_size, data, GL_DYNAMIC_DRAW);

    if (report_possible_error("Unable to create a new OpenGL buffer object."))
        return -1;

    return buffer_glo;
}


int 
opengl_write_buffer(unsigned int buffer_glo, size_t offset, size_t size, void *data)
{
    int exitcode = 0;

    glBindBuffer(GL_ARRAY_BUFFER, buffer_glo);
    glBufferSubData(GL_ARRAY_BUFFER, offset, size, data);

    if (report_possible_error("Unable to write to OpenGL buffer."))
        exitcode = -1;

    return exitcode;
}


int
opengl_read_buffer(unsigned int buffer_glo, size_t offset, size_t size, void *data)
{
    int exitcode = 0;
    glBindBuffer(GL_ARRAY_BUFFER, buffer_glo);
    glGetBufferSubData(GL_ARRAY_BUFFER, offset, size, data);

    if (report_possible_error("Unable to read OpenGL buffer."))
        exitcode = -1;

    return exitcode;
}


void 
opengl_release_buffer(unsigned int buffer_glo)
{
    GLuint glo = buffer_glo;
    glDeleteBuffers(1, &glo);
}


const char *
opengl_get_error(void)
{
    const char *rv = *error_message;
    clear_error();
    return rv;
}


static void clear_error(void)
{
    err_occurred = false;
    error_message = NULL;
}


static bool
report_possible_error(const char *msg)
{
    if (!check_errors())
        return false;
    if (error_message != NULL)
        return true;

    error_message = &msg;
    return true;
}


static bool 
check_errors(void) 
{
    GLenum err;
    while ((err=glGetError()) != GL_NO_ERROR)
        err_occurred = true;
    return err_occurred;
}


void GLAPIENTRY
gl_error_callback(GLenum source,
                  GLenum type,
                  GLuint id,
                  GLenum severity,
                  GLsizei length,
                  const GLchar* message,
                  const void* userParam)
{
    if (type == GL_DEBUG_TYPE_ERROR)
        error_message = &message;
}
