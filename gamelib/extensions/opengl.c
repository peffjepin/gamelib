#include <stdlib.h>
#include <stdbool.h>
#include <string.h>

#include <glad.h>
#include "opengl.h"

static bool initialized = false;

char *opengl_error = NULL;
size_t opengl_error_length = 0;

static bool should_free_error = false;
#define OPENGL_ERROR_OCCURRED opengl_error_length > 0

static bool report_possible_error(const char *msg);
static bool check_errors(void);
#define OPENGL_SET_ERROR(msg, len, should_free) {\
                opengl_error = msg;\
                opengl_error_length = len;\
                should_free_error = should_free;\
}

void GLAPIENTRY gl_error_callback(GLenum source, GLenum type, GLuint id, 
                                  GLenum severity, GLsizei length, 
                                  const GLchar* message, const void* userParam);

static bool opengl_shader_compilation_successful(GLuint shader_id);
static bool opengl_program_linking_successful(GLuint program_id);


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
    GLuint buffer_id;
    glGenBuffers(1, &buffer_id);
    glBindBuffer(GL_ARRAY_BUFFER, buffer_id);
    glBufferData(GL_ARRAY_BUFFER, buffer_size, data, GL_DYNAMIC_DRAW);

    if (report_possible_error("Unable to create a new OpenGL buffer object."))
        return -1;

    return buffer_id;
}


int 
opengl_write_buffer(unsigned int buffer_id, size_t offset, size_t size, void *data)
{
    int exitcode = 0;

    glBindBuffer(GL_ARRAY_BUFFER, buffer_id);
    glBufferSubData(GL_ARRAY_BUFFER, offset, size, data);

    if (report_possible_error("Unable to write to OpenGL buffer."))
        exitcode = -1;

    return exitcode;
}


int
opengl_read_buffer(unsigned int buffer_id, size_t offset, size_t size, void *data)
{
    int exitcode = 0;
    glBindBuffer(GL_ARRAY_BUFFER, buffer_id);
    glGetBufferSubData(GL_ARRAY_BUFFER, offset, size, data);

    if (report_possible_error("Unable to read OpenGL buffer."))
        exitcode = -1;

    return exitcode;
}


inline void 
opengl_release_buffer(unsigned int buffer_id)
{
    glDeleteBuffers(1, (GLuint *) &buffer_id);
}


#include <stdio.h>
int 
opengl_create_shader_stage(unsigned int shader_type, const char *source)
{
    GLuint shader_id = glCreateShader((GLenum) shader_type);
    glShaderSource(shader_id, 1, &source, NULL);
    glCompileShader(shader_id);
    
    if (!opengl_shader_compilation_successful(shader_id)) {
        glDeleteShader(shader_id); 
        return -1;
    }

    return shader_id;
}


static bool
opengl_shader_compilation_successful(GLuint shader_id)
{
    GLint gl_status = 0;
    glGetShaderiv(shader_id, GL_COMPILE_STATUS, &gl_status);
    bool success = (gl_status == GL_TRUE) ? true : false;

    if (!success) {
        GLint error_length = 0;
        glGetShaderiv(shader_id, GL_INFO_LOG_LENGTH, &error_length);

        char *error = malloc(error_length);
        glGetShaderInfoLog(shader_id, error_length, &error_length, error);

        OPENGL_SET_ERROR(error, error_length, true);
    }

    return success;
}


int
opengl_create_program(unsigned int shaders[], size_t length)
{
    GLuint program_id = glCreateProgram();

    for (int i = 0; i < length; i++) {
        glAttachShader(program_id, shaders[i]);
    }

    glLinkProgram(program_id);

    // cleanup everything on unsucessful linking
    if (!opengl_program_linking_successful(program_id)) {
        for (int i = 0; i < length; i++) {
            GLuint shader_id = shaders[i];
            glDetachShader(program_id, shader_id);
            glDeleteShader(shader_id);
        }
        glDeleteProgram(program_id);
        return -1;
    }
    // detatch shaders after successful linking
    else {
        for (int i = 0; i < length; i++) {
            GLuint shader_id = shaders[i];
            glDetachShader(program_id, shader_id);
        }
    }

    return program_id;
}


static bool 
opengl_program_linking_successful(GLuint program_id)
{
    GLint status = 0;
    glGetProgramiv(program_id, GL_LINK_STATUS, &status);
    bool success = (status == GL_TRUE) ? true : false;

    if (!success) {
        GLint error_length = 0;
        glGetProgramiv(program_id, GL_INFO_LOG_LENGTH, &error_length);

        char *error = malloc(error_length);
        glGetProgramInfoLog(program_id, error_length, &error_length, error);

        OPENGL_SET_ERROR(error, error_length, true);
    }
	
    return success;
}


inline void 
opengl_release_shader(unsigned int shader_id)
{
    glDeleteShader(shader_id);
}


inline void 
opengl_release_program(unsigned int program_id)
{
    glDeleteProgram(program_id);
}


void opengl_clear_error(void)
{
    if (should_free_error)
        free(opengl_error);

    opengl_error = NULL;
    opengl_error_length = 0;
}


static bool
report_possible_error(const char *msg)
{
    if (!check_errors())
        return false;
    if (opengl_error_length > 0)
        // error might be already set from gl_error_callback
        return true;

    OPENGL_SET_ERROR((char *)msg, strlen(msg), false);
    return true;
}


static bool 
check_errors(void) 
{
    // if the debug output is available then the error message will be set
    // by gl_error_callback, otherwise the caller will have to set an error
    GLenum err;
    bool error_occurred = false;
    while ((err=glGetError()) != GL_NO_ERROR)
        error_occurred = true;
    return error_occurred;
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
    if (type == GL_DEBUG_TYPE_ERROR) {
        OPENGL_SET_ERROR((char *) message, length, false);
    }
}
