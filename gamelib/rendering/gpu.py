import numpy as np

import gamelib
from gamelib import gl
from gamelib.rendering import glslutils
from gamelib.rendering import buffers


class GPUInstructions:
    """Common functions for issuing commands to the gpu."""

    def __init__(self, shader, **data_sources):
        """Initialize a new instruction.

        Parameters
        ----------
        shader : Any
            This should either be a single source string or a filename for the
            shader to be used. See glslutils.py docstring for more info.
        **data_sources : Any
            The keys should map to inputs for the specified shader and the
            values can be either np.ndarrays or buffers.Buffer instances.
        """

        if isinstance(shader, str) and "#version" in shader:
            self.shader = glslutils.ShaderData.read_string(shader)
        else:
            self.shader = glslutils.ShaderData.read_file(shader)
        self.vao = VertexArray(self.shader, **data_sources)

    def source(self, **data_sources):
        """Use these data sources."""

        self.vao.use_sources(**data_sources)


class TransformFeedback(GPUInstructions):
    """Use the GPU to transform some data."""

    def __init__(self, shader, **data_sources):
        super().__init__(shader)
        self.sources = data_sources

    def source(self, **data_sources):
        self.sources.update(data_sources)

    def transform(self, vertices=None, **data_sources):
        """Issue the transform feedback command. This will block and read back
        the buffer into a np.ndarray.

        Parameters
        ----------
        vertices : optional, int
            How many vertices to transform. If not given the VertexArray will
            try to calculate it based on buffer lengths.
        **data_sources : Any
            If not provided in __init__ the input buffers can be given now.

        Returns
        -------
        np.ndarray:
            This will return a structured array if the shader has multiple
            outputs, otherwise it will be a regular array converted to the
            output datatype.
        """

        self.sources.update(data_sources)
        vao = VertexArray(self.shader, **self.sources)
        vao.update()
        out_dtype = np.dtype(
            [
                (desc.name, desc.dtype)
                for desc in self.shader.meta.vertex_outputs.values()
            ]
        )
        vertices = vertices or vao.num_elements
        reserve = vertices * out_dtype.itemsize
        result_buffer = gamelib.get_context().buffer(reserve=reserve)
        vao.glo.transform(result_buffer, vertices=vertices)
        array = np.frombuffer(result_buffer.read(), out_dtype)
        if len(self.shader.meta.vertex_outputs) == 1:
            return array[next(iter(self.shader.meta.vertex_outputs.keys()))]
        return array


class Renderer(GPUInstructions):
    """Issues draw calls."""

    def render(self, vertices=None):
        self.vao.update()
        vertices = vertices or self.vao.num_elements
        self.vao.glo.render(vertices=vertices)


class VertexArray:
    """Responsible for mapping data on the CPU side to shader inputs on the
    GPU."""

    def __init__(
        self,
        shader,
        instanced=(),
        indices=None,
        auto=True,
        mode=gl.TRIANGLES,
        **data_sources,
    ):
        """Initialize a vertex array.

        Parameters
        ----------
        shader : ShaderData
        instanced : optional, Sequence
        indices : optional, np.ndarray | buffers.Buffer
        auto : optional, bool
        mode : optional, int
        **data_sources : Any
            The keys must map to either a buffer or uniform within the
            given shader. The values for buffers can be either np.ndarray or
            buffers.Buffer. The uniforms can be either np.ndarray or python
            values.
        """

        self._glo = None
        self._dirty = True
        self._auto = auto
        self._mode = mode
        self._index_buffer = None
        self._instanced_attibutes = set(instanced)
        self._buffers_in_use = dict()
        self._uniforms_in_use = dict()
        self._generated_buffers = list()

        # TODO: At some point this needs to change so multiple vertex arrays
        #   can use the same OpenGL shader object. ShaderData could make a
        #   hash and the OpenGL shader objects can come from one global
        #   that will cache the shaders for each unique ShaderData hash.
        self.shader = shader
        self._shader_glo = gamelib.get_context().program(
            vertex_shader=shader.code.vert,
            tess_control_shader=shader.code.tesc,
            tess_evaluation_shader=shader.code.tese,
            geometry_shader=shader.code.geom,
            fragment_shader=shader.code.frag,
            varyings=shader.meta.vertex_outputs,
        )
        self.use_sources(**data_sources)
        self.source_indices(indices)

    @property
    def glo(self):
        """The underlying moderngl object."""

        if self._glo is None or self._dirty:
            self._make_glo()
        return self._glo

    @property
    def num_elements(self):
        """The number of elements that are detected to be in the current
        buffers. This is first by an index buffer if present, otherwise by
        the smallest buffer.

        Returns
        -------
        int
        """

        if self._index_buffer:
            return len(self._index_buffer)
        else:
            lengths = [len(vbo) for vbo in self._buffers_in_use.values()]
            return min(lengths)

    @property
    def _buffer_format_tuples(self):
        """(buffer_obj, buffer_format, buffer_name) formatting tuples."""

        format_tuples = []
        for name, buffer in self._buffers_in_use.items():
            moderngl_attr = self._shader_glo[name]
            strtype = moderngl_attr.shape
            if strtype == "I":
                # conform to moderngl expected strfmt dtypes
                # eventually I'd like to move towards doing
                # all the shader source code inspection myself,
                # as the moderngl api doesn't offer all the
                # metadata I would like it to and weird issues
                # like this one.
                strtype = "u"
            strfmt = f"{moderngl_attr.dimension}{strtype}"
            format_tuples.append((buffer.gl, strfmt, name))
        return format_tuples

    def update(self):
        """Updates _AutoUniform and AutoBuffer objects."""

        for buffer in self._buffers_in_use.values():
            if isinstance(buffer, buffers.AutoBuffer):
                buffer.update()
        for uniform in self._uniforms_in_use.values():
            uniform.update(self._shader_glo)

    def use_source(self, name, source):
        """Set a source uniform/buffer.

        Parameters
        ----------
        name : str
        source : np.ndarray | buffers.Buffer | Any
            If sourcing a buffer, this should be either a np.ndarray or a
            buffers.Buffer.
            If sourcing a uniform this can be a np.ndarray or a python number
            or tuple.
        """

        if name in self.shader.meta.attributes:
            self._integrate_buffer(name, source)
        elif name in self.shader.meta.uniforms:
            self._integrate_uniform(name, source)
        else:
            self._raise_invalid_source(name)

    def use_sources(self, **data_sources):
        """Shorthand for many use_source calls. See use_source"""

        for name, source in data_sources.items():
            self.use_source(name, source)

    def source_buffers(self, **buffer_sources):
        """Set a buffer source.

        Parameters
        ----------
        buffer_sources : buffers.Buffer | np.ndarray
        """

        for name, buffer in buffer_sources.items():
            self._integrate_buffer(name, buffer)

    def source_indices(self, indices):
        """Set the index buffer.

        Parameters
        ----------
        indices : np.ndarray | buffers.Buffer
        """

        if self._index_buffer is not None:
            if isinstance(indices, np.ndarray):
                self._index_buffer.write(indices)
            elif isinstance(indices, buffers.Buffer):
                self._remove_buffer(self._index_buffer)
                self._index_buffer = indices
        else:
            self._index_buffer = self._generate_buffer(
                indices, gl.uint, auto=False
            )

    def source_uniforms(self, **uniform_sources):
        """Source uniform values.

        Parameters
        ----------
        uniform_sources : np.ndarray | tuple | int | float
            If sourced with a np.ndarray, this uniform will continually be
            updated from that array.
            If sourced from a python value it will set the value just once.
        """

        for name, uniform in uniform_sources.items():
            self._integrate_uniform(name, uniform)

    def _integrate_buffer(self, attribute, source):
        if attribute not in self.shader.meta.attributes:
            self._raise_invalid_source(attribute)

        current_buffer = self._buffers_in_use.get(attribute, None)
        if current_buffer is None:
            dtype = self.shader.meta.attributes[attribute].dtype
            buffer = self._generate_buffer(source, dtype)
            self._buffers_in_use[attribute] = buffer
        else:
            if isinstance(source, buffers.Buffer):
                self._remove_buffer(current_buffer)
                self._buffers_in_use[attribute] = source
            elif isinstance(source, np.ndarray):
                if isinstance(current_buffer, buffers.AutoBuffer):
                    current_buffer.use_array(source)
                else:
                    current_buffer.write(source)

    def _integrate_uniform(self, name, source):
        if isinstance(source, np.ndarray):
            dtype = self.shader.meta.uniforms[name].dtype
            self._uniforms_in_use[name] = _AutoUniform(source, dtype, name)
        else:
            self._shader_glo[name] = value
            self.gl[name] = value

    def _generate_buffer(self, source, dtype, auto=None):
        self._dirty = True
        if isinstance(source, buffers.Buffer):
            return source
        elif isinstance(source, np.ndarray):
            auto = auto if auto is not None else self._auto
            buf_type = buffers.AutoBuffer if auto else buffers.Buffer
            buf = buf_type(source, dtype)
            self._generated_buffers.append(buf)
            return buf

    def _remove_buffer(self, buffer):
        self._dirty = True
        if buffer in self._generated_buffers:
            self._generated_buffers.remove(buffer)
            buffer.gl.release()

    def _make_glo(self):
        if self._glo is not None:
            self._glo.release()
        ibo = self._index_buffer.gl if self._index_buffer else None
        self._glo = gamelib.get_context().vertex_array(
            self._shader_glo,
            self._buffer_format_tuples,
            index_buffer=ibo,
            index_element_size=4,
        )
        self._dirty = False

    def _raise_invalid_source(self, name):
        raise ValueError(
            f"{name!r} is not a valid uniform/buffer name for this shader. "
            f"Valid uniforms: {tuple(self.shader.meta.uniforms.keys())!r}, "
            f"valid buffers: {tuple(self.shader.meta.attributes.keys())!r}"
        )


class _AutoUniform:
    """Helper class for ShaderProgram to keep track of uniform sources."""

    def __init__(self, array, dtype, name):
        """
        Parameters
        ----------
        array : np.ndarray
        dtype : np.dtype | str
        name : str
        """
        self.array = array
        self.dtype = dtype
        self.name = name

    def update(self, prog):
        prog[self.name].write(self._data)

    @property
    def _data(self):
        return gl.coerce_array(self.array, self.dtype).tobytes()