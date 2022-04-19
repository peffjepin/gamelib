#ifndef GAMELIB_BUFFER_H
#define GAMELIB_BUFFER_H

#include <stdint.h>
#include <stddef.h>

void opengl_initialize(void);

int opengl_create_buffer(size_t buffer_size, void *data);
/* returns object id on success else -1 
 */

void opengl_initialize(void);
const char *opengl_get_error(void);
int opengl_write_buffer(unsigned int buffer_glo, size_t offset, size_t size, void *data);
int opengl_read_buffer(unsigned int buffer_glo, size_t offset, size_t size, void* data);
void opengl_release_buffer(unsigned int buffer_glo);

#endif // GAMELIB_BUFFER_H
