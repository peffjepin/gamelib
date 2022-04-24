#ifndef GAMELIB_BUFFER_H
#define GAMELIB_BUFFER_H

#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include <glad.h>

extern size_t opengl_error_length;
extern char *opengl_error;

void opengl_clear_error(void);
#define OPENGL_CONSUME_ERROR(name) char name[opengl_error_length];\
                                   strcpy(name, opengl_error);\
                                   opengl_clear_error()

void opengl_initialize(void);

/* returns object id on success else -1 
 */
int opengl_create_buffer(size_t buffer_size, void *data);
int opengl_write_buffer(unsigned int buffer_id, size_t offset, size_t size, void *data);
int opengl_read_buffer(unsigned int buffer_id, size_t offset, size_t size, void* data);
void opengl_release_buffer(unsigned int buffer_id);

int opengl_create_shader_stage(unsigned int shader_type, const char *source);
int opengl_create_program(unsigned int shaders[], size_t length);
void opengl_release_shader(unsigned int shader_id);
void opengl_release_program(unsigned int program_id);

#endif // GAMELIB_BUFFER_H
