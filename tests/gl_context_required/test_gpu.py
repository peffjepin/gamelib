import time

import numpy as np
import pytest
import gamelib

from gamelib import rendering
from gamelib.core import resources, gl
from gamelib.rendering import buffers
from gamelib.rendering import gpu
from gamelib.rendering import shaders
from ..conftest import assert_approx


@pytest.fixture(autouse=True, scope="module")
def init_ctx():
    gamelib.init(headless=True)
    yield gamelib.get_context()


class TestVertexArray:
    shader_source = """
        #version 330
        #vert
        in vec3 v_pos;
        void main() {
            gl_Position = vec4(v_pos, 1.0);
        }
        #frag
        uniform vec4 f_color;
        out vec4 frag;
        void main() {
            frag = f_color;
        }
    """

    @pytest.fixture
    def shader(self):
        return shaders.Shader(src=self.shader_source)

    def test_init(self, shader):
        vao = gpu.VertexArray(
            shader, v_pos=np.arange(9), f_color=np.array([1.0, 1.0, 1.0, 1.0])
        )

        assert vao.glo is not None

    def test_same_internal_shader_object(self, shader):
        vao1 = gpu.VertexArray(
            shader, v_pos=np.arange(9), f_color=np.array([1.0, 1.0, 1.0, 1.0])
        )
        vao2 = gpu.VertexArray(
            shader, v_pos=np.arange(9), f_color=np.array([1.0, 1.0, 1.0, 1.0])
        )

        assert vao1.shader is vao2.shader

    def test_sourcing_an_attached_buffer_with_an_array(self, shader):
        buffer = buffers.Buffer(np.arange(9), gl.vec3)
        vao = gpu.VertexArray(shader, v_pos=buffer, f_color=np.arange(4))

        array = np.arange(18, dtype=gl.vec3)
        vao.source_buffers(v_pos=array)

        assert np.all(buffer.read() == array)

    def test_sourcing_an_attached_buffer_with_a_list(self, shader):
        buffer = buffers.Buffer(np.arange(9), gl.vec3)
        vao = gpu.VertexArray(shader, v_pos=buffer, f_color=np.arange(4))

        list_ = [(1, 2, 3), (3, 2, 1)]
        array = np.array(list_, dtype=gl.vec3)
        vao.source_buffers(v_pos=list_)

        assert np.all(buffer.read() == array)

    def test_sourcing_an_attached_autobuffer_with_an_array(self, shader):
        buffer = buffers.AutoBuffer(np.array((1, 2, 3)), gl.vec3)
        vao = gpu.VertexArray(shader, v_pos=buffer, f_color=np.arange(4))

        array = gl.coerce_array(np.arange(18), gl.vec3)
        vao.source_buffers(v_pos=array)
        array += 100
        buffer.update()

        assert np.all(buffer.read() == array)

    def test_updates_autobuffers(self, shader):
        array = gl.coerce_array(np.arange(18), gl.vec3)
        buffer = buffers.AutoBuffer(array, gl.vec3)
        vao = gpu.VertexArray(shader, v_pos=buffer, f_color=np.arange(4))

        array += 100
        vao.update()

        assert np.all(buffer.read() == array)

    def test_creates_new_glo_if_buffer_glo_changes(self, shader):
        array = gl.coerce_array(np.arange(18), gl.vec3)
        buffer = buffers.Buffer(array, gl.vec3)
        vao = gpu.VertexArray(shader, v_pos=buffer, f_color=np.arange(4))
        identity = id(vao.glo)

        buffer.write(np.arange(27))
        # new buffer will require new moderngl vertex array object
        assert id(vao.glo) != identity

    def test_num_entities_governed_by_smallest_buffer(self):
        array1 = np.arange(12)
        array2 = np.arange(12)
        shader = shaders.Shader(
            src="""
            #version 330
            #vert
            in int input1;
            in vec2 input2;
            out int output1;
            out vec2 output2;
            void main()
            {
                output1 = input1;
                output2 = input2;
            }
        """
        )
        vao = gpu.VertexArray(shader, input1=array1, input2=array2)
        assert vao.num_elements == 6

        vao.source_buffers(input2=np.arange(20))
        assert vao.num_elements == 10

        vao.source_buffers(input2=np.arange(100))
        assert vao.num_elements == 12

    def test_num_elements_with_index_buffer(self):
        index_array = np.arange(8)
        input_array = np.arange(10)
        shader = shaders.Shader(
            src="""
            #version 330
            #vert
            in int test_in;
            out int test_out;
            void main()
            {
                test_out = test_in;
            }
            """
        )
        program = gpu.VertexArray(
            shader,
            test_in=input_array,
            indices=index_array,
        )

        assert program.num_elements == 8

        program.source_buffers(test_in=np.arange(4))
        assert program.num_elements == 8

    def test_num_instances(self):
        shader = shaders.Shader(
            src="""
            #version 330
            #vert
            in vec3 v_pos;
            in float scale;

            void main() {
                gl_Position = vec4(v_pos * scale, 1);
            }

            #frag
            out vec4 frag;
            void main() {
                frag = vec4(1, 1, 1, 1);
            }
        """
        )
        vao = gpu.VertexArray(
            shader,
            v_pos=np.array([(0, 1, 2), (0, 2, 3), (1, 2, 3)]),
            scale=np.array([1, 2, 3, 4, 5]),
            instanced=("scale",),
        )

        assert vao.num_instances == 5
        assert vao.num_elements == 3


class TestTransformFeedback:
    def test_base_case(self):
        data_in = np.arange(10, dtype=gl.float)
        instructions = gpu.TransformFeedback(
            shader="""
                #version 330
                #vert
                in float data_in;
                out float data_out;
                void main() {
                    data_out = 2 * data_in;
                }
            """
        )
        assert_approx(data_in * 2, instructions.transform(data_in=data_in))

    def test_multiple_outputs(self):
        data_in = np.arange(10, dtype=gl.float)
        instructions = gpu.TransformFeedback(
            shader="""
            #version 330
            #vert
            in float data_in;
            out float data_out1;
            out float data_out2;
            void main() {
                data_out1 = 2 * data_in;
                data_out2 = 3 * data_in;
            }
            """
        )

        transformed = instructions.transform(data_in=data_in)
        assert_approx(data_in * 2, transformed["data_out1"])
        assert_approx(data_in * 3, transformed["data_out2"])


class TestVaoIntegration:
    """Use TransformFeedback to send live data to the gpu for testing."""

    def test_automatic_uniform_sourcing(self, glsl_dtype_and_input):
        gl_type, input_value = glsl_dtype_and_input
        if gl_type == "sampler2D" or gl_type.startswith("b"):
            # not applicable
            return

        uniform = np.array(input_value)
        instructions = gpu.TransformFeedback(
            shader=f"""
                #version 400
                #vert
                uniform {gl_type} test_input;
                out {gl_type} test_output;
                void main()
                {{
                    test_output = test_input;
                }}
            """,
            test_input=uniform,
        )

        expected = gl.coerce_array(uniform, gl_type)
        assert instructions.transform(1).tobytes() == expected.tobytes()

        uniform += 1
        expected = gl.coerce_array(uniform, gl_type)
        assert instructions.transform(1).tobytes() == expected.tobytes()

    def test_uniform_array_support(self, glsl_dtype_and_input):
        gl_type, input_value = glsl_dtype_and_input
        if gl_type == "sampler2D" or gl_type.startswith("b"):
            # not applicable
            return

        arr1 = np.array(input_value)
        arr2 = arr1 + 7
        uniform = np.stack((arr1, arr2))
        instructions = gpu.TransformFeedback(
            shader=f"""
                #version 400
                #vert
                uniform {gl_type} test_input[2];
                out {gl_type} test_output;
                void main()
                {{
                    test_output = test_input[gl_VertexID];
                }}
            """,
            test_input=uniform,
        )

        expected = gl.coerce_array(uniform, gl_type)
        assert (
            instructions.transform(vertices=2).tobytes() == expected.tobytes()
        )

    def test_use_uniforms_no_current_uniforms(self):
        instructions = gpu.TransformFeedback(
            """
            #version 330
            #vert
            uniform int input1;
            uniform int input2;
            out int output_value;
            void main()
            {
                output_value = input1 + input2;
            }
            """
        )
        uni1, uni2 = np.array([0], gl.int), np.array([100], gl.int)
        instructions.source(input1=uni1, input2=uni2)
        assert instructions.transform(1) == uni1 + uni2

        uni1 += 12
        uni2 += 11
        assert instructions.transform(1) == uni1 + uni2

    def test_use_uniforms_with_existing_uniforms_in_place(self):
        uni1, uni2 = np.array([0], gl.int), np.array([100], gl.int)
        instructions = gpu.TransformFeedback(
            shader="""
                #version 330
                #vert
                uniform int input1;
                uniform int input2;
                out int output_value;
                void main()
                {
                    output_value = input1 + input2;
                }
            """,
            input1=uni1,
            input2=uni2,
        )
        assert instructions.transform(1) == uni1 + uni2

        uni3, uni4 = np.array([9], gl.int), np.array([120], gl.int)
        instructions.source(input1=uni3, input2=uni4)
        assert instructions.transform(1) == uni3 + uni4

        uni3 += 12
        uni4 += 11
        assert instructions.transform(1) == uni3 + uni4

    def test_use_buffers_no_current_buffers(self):
        instructions = gpu.TransformFeedback(
            """
            #version 330
            #vert
            in int input1;
            in int input2;
            out int output_value;
            void main()
            {
                output_value = input1 + input2;
            }
            """
        )
        array1 = np.arange(6, dtype=gl.int)
        array2 = np.arange(6, 12, dtype=gl.int)

        instructions.source(input1=array1, input2=array2)
        assert np.all(instructions.transform() == array1 + array2)

        array1 += 10
        array2 += 20
        assert np.all(instructions.transform() == array1 + array2)

    def test_use_buffer_buffers_already_there(self):
        array1 = np.arange(6, dtype=gl.int)
        array2 = np.arange(6, 12, dtype=gl.int)
        instructions = gpu.TransformFeedback(
            shader="""
                #version 330
                #vert
                in int input1;
                in int input2;
                out int output_value;
                void main()
                {
                    output_value = input1 + input2;
                }
            """,
            input1=array1,
            input2=array2,
        )
        assert np.all(instructions.transform() == array1 + array2)

        array3 = np.arange(100, dtype=gl.int)
        array4 = np.arange(100, dtype=gl.int)
        instructions.source(input1=array3, input2=array4)

        assert np.all(instructions.transform() == array3 + array4)

        array3 += 100
        array4 += 33
        assert np.all(instructions.transform() == array3 + array4)

    def test_using_a_callable_as_a_source(self):
        array1 = np.arange(6, dtype=gl.int)
        proxy = lambda: array1
        instructions = gpu.TransformFeedback(
            shader="""
                #version 330
                #vert
                in int input1;
                out int output_value;
                void main()
                {
                    output_value = input1;
                }
            """,
            input1=proxy,
        )
        assert np.all(instructions.transform() == array1)

        array1 = np.arange(12)

        assert np.all(instructions.transform() == array1)

    def test_using_a_list_as_a_source(self):
        list1 = [(100, 10, 1), (100, 20, 3)]
        list2 = [(100, 10, 1), (100, 20, 3), (100, 10, 1), (100, 20, 3)]

        instructions = gpu.TransformFeedback(
            shader="""
                #version 330
                #vert
                in vec3 in_value;
                out int out_value;
                void main()
                {
                    out_value = int(in_value.x + in_value.y + in_value.z);
                }
            """,
            in_value=list1,
        )
        assert np.all(instructions.transform() == [111, 123])

        instructions.source(in_value=list2)

        assert np.all(instructions.transform() == [111, 123, 111, 123])

    def test_automatic_hot_reloading_shaders_when_the_new_shader_is_valid(
        self, write_shader_to_disk
    ):
        src = """
            #version 330
            #vert
            const int test_val = %s;
            out int out_val;
            void main()
            {
                out_val = test_val;
            }
        """
        write_shader_to_disk("test", src % 123)
        instructions = gpu.TransformFeedback(
            "test", automatic_hot_reloading=True
        )

        assert instructions.transform(1) == 123

        time.sleep(0.01)
        write_shader_to_disk("test", src % 321)
        assert instructions.transform(1) == 321

    def test_automatic_hot_reloading_shaders_when_the_new_shader_is_invalid(
        self, write_shader_to_disk
    ):
        src = """
            #version 330
            #vert
            const int test_val = %s;
            out int out_val;
            void main()
            {
                out_val = test_val;
            }
        """
        write_shader_to_disk("test", src % 123)
        instructions = gpu.TransformFeedback(
            "test", automatic_hot_reloading=True
        )

        assert instructions.transform(1) == 123

        time.sleep(0.01)
        write_shader_to_disk("test", src % "invalid")
        assert instructions.transform(1) == 123


class TestUniformBlock:
    @staticmethod
    def make_instructions(**uniform_descs):
        uni_declarations = "\n".join(
            f"uniform {type} {name};" for name, type in uniform_descs.items()
        )
        out_declarations = "\n".join(
            f"out {type} {'out_' + name};"
            for name, type in uniform_descs.items()
        )
        out_assignments = "\n".join(
            f"out_{name} = {name};" for name in uniform_descs
        )
        return gpu.TransformFeedback(
            f"""
        #version 330
        #vert
        {uni_declarations}
        {out_declarations}

        void main()
        {{
            {out_assignments}
        }}
        """
        )

    def test_sourcing_instructions(self):
        class MyBlock(rendering.uniforms.UniformBlock):
            offset = rendering.uniforms.ArrayStorage(gl.vec2)
            scale = rendering.uniforms.ArrayStorage(gl.float)

        block = MyBlock(offset=(1, 2), scale=3)
        inst = self.make_instructions(offset="vec2", scale="float")
        inst.source(**block.todict())

        result = inst.transform(1)
        assert np.all(result["out_offset"] == (1, 2))
        assert result["out_scale"] == 3

    def test_updates_are_seen_in_instructions(self):
        class MyBlock(rendering.uniforms.UniformBlock):
            offset = rendering.uniforms.ArrayStorage(gl.vec2)
            scale = rendering.uniforms.ArrayStorage(gl.float)

        block = MyBlock(offset=(1, 2), scale=3)
        inst = self.make_instructions(offset="vec2", scale="float")
        inst.source(**block.todict())

        block.offset = (3, 4)
        block.scale = 5

        result = inst.transform(1)
        assert np.all(result["out_offset"] == (3, 4))
        assert result["out_scale"] == 5

    def test_cursor_screen_space(self):
        gamelib.get_cursor = lambda: (12, 34)
        gamelib.get_width = lambda: 100
        gamelib.get_height = lambda: 100
        gamelib.update()
        inst = self.make_instructions(cursor="vec2")

        assert np.allclose(inst.transform(1), (12 / 100, 34 / 100))

    def test_view_mat4(self):
        camera = rendering.PerspectiveCamera((123, 123, 123), (1, 3, 2))
        camera.set_primary()
        gamelib.update()
        inst = self.make_instructions(view="mat4")

        assert np.allclose(inst.transform(1), camera.view_matrix)

    def test_proj_mat4(self):
        camera = rendering.PerspectiveCamera((123, 123, 123), (1, 3, 2))
        camera.set_primary()
        gamelib.update()
        inst = self.make_instructions(proj="mat4")

        assert np.allclose(inst.transform(1), camera.proj_matrix)

    def test_window_size(self):
        gamelib.get_width = lambda: 16
        gamelib.get_height = lambda: 9
        gamelib.update()
        inst = self.make_instructions(window_size="ivec2")

        assert np.allclose(inst.transform(1), [16, 9])
