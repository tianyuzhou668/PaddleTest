import os
if os.getenv('FLAGS_cinn_new_group_scheduler') is None:
    os.environ['FLAGS_cinn_new_group_scheduler'] = '1'
if os.getenv('FLAGS_group_schedule_tiling_first') is None:
    os.environ['FLAGS_group_schedule_tiling_first'] = '1'
if os.getenv('FLAGS_prim_all') is None:
    os.environ['FLAGS_prim_all'] = 'true'
if os.getenv('FLAGS_prim_enable_dynamic') is None:
    os.environ['FLAGS_prim_enable_dynamic'] = '1'
if os.getenv('FLAGS_enable_pir_api') is None:
    os.environ['FLAGS_enable_pir_api'] = '1'
if os.getenv('FLAGS_cinn_bucket_compile') is None:
    os.environ['FLAGS_cinn_bucket_compile'] = '1'

import unittest
import numpy as np
import paddle

def GetEnvVarEnableJit():
    enable_jit = os.getenv('PADDLE_DEBUG_ENABLE_JIT')
    return enable_jit not in {
        "0",
        "False",
        "false",
        "OFF",
    }

def GetEnvVarEnableCinn():
    enable_cinn = os.getenv('PADDLE_DEBUG_ENABLE_CINN')
    if enable_cinn is None:
        return True
    return enable_cinn not in {
        "0",
        "False",
        "false",
        "OFF",
    }


def GetTolerance(dtype):
    if dtype == np.float16:
        return GetFloat16Tolerance()
    if dtype == np.float32:
        return GetFloat32Tolerance()
    return 1e-6

def GetFloat16Tolerance():
    try:
        return float(os.getenv('PADDLE_DEBUG_FLOAT16_TOL'))
    except:
        return 1e-3

def GetFloat32Tolerance():
    try:
        return float(os.getenv('PADDLE_DEBUG_FLOAT32_TOL'))
    except:
        return 1e-6

def IsInteger(dtype):
    return np.dtype(dtype).char in np.typecodes['AllInteger']

def ApplyToStatic(net, use_cinn):
    build_strategy = paddle.static.BuildStrategy()
    build_strategy.build_cinn_pass = use_cinn
    return paddle.jit.to_static(
        net,
        input_spec=net.get_input_spec(),
        build_strategy=build_strategy,
        full_graph=True,
    )

class InstanceTrait:

    @classmethod
    def instance(cls):
        if cls.instance_ is None:
            cls.instance_ = cls()
        return cls.instance_

    @classmethod
    def static_instance_with_cinn(cls):
        if cls.static_instance_with_cinn_ is None:
            cls.static_instance_with_cinn_ = ApplyToStatic(
                cls.instance(),
                use_cinn=True
            )
        return cls.static_instance_with_cinn_

    @classmethod
    def static_instance_without_cinn(cls):
        if cls.static_instance_without_cinn_ is None:
            cls.static_instance_without_cinn_ = ApplyToStatic(
                cls.instance(),
                use_cinn=False
            )
        return cls.static_instance_without_cinn_


class CinnTestBase:

    def setUp(self):
        paddle.seed(2024)
        self.prepare_data()

    def test_train(self):
        dy_outs = self.train(use_cinn=False)
        cinn_outs = self.train(use_cinn=GetEnvVarEnableCinn())

        for cinn_out, dy_out in zip(cinn_outs, dy_outs):
          if type(cinn_out) is list and type(dy_out) is list:
            for x, y in zip(cinn_out, dy_out):
              self.assert_all_close(x, y)
          else:
            self.assert_all_close(cinn_out, dy_out)

    def train(self, use_cinn):
        if GetEnvVarEnableJit():
            net = self.prepare_static_net(use_cinn)
        else:
            net = self.prepare_net()
        out = net(*self.inputs)
        return out
    
    def prepare_data(self):
        self.inputs = self.get_inputs()
        for input in self.inputs:
            input.stop_gradient = True

    def prepare_net(self):
        return self.get_test_class().instance()

    def prepare_static_net(self, use_cinn):
        if use_cinn:
            return self.get_test_class().static_instance_with_cinn()
        else:
            return self.get_test_class().static_instance_without_cinn()

    def assert_all_close(self, x, y):
        if (hasattr(x, "numpy") and hasattr(y, "numpy")):
            x_numpy = x.numpy()
            y_numpy = y.numpy()
            assert x_numpy.dtype == y_numpy.dtype
            if IsInteger(x_numpy.dtype):
                np.testing.assert_equal(x_numpy, y_numpy)
            else:
                tol = GetTolerance(x_numpy.dtype)
                np.testing.assert_allclose(x_numpy, y_numpy, atol=tol, rtol=tol)
        else:
            assert x == y



class PrimitiveOp_8a52759e16f03d4d5b0bd5ecb58d0bd7(InstanceTrait, paddle.nn.Layer):
    
    def __init__(self):
        super().__init__()

    def forward(self, input_0, input_1):
        return paddle._C_ops.full_with_tensor(input_0, input_1, paddle.float32)

    def get_input_spec(self):
        return [
            paddle.static.InputSpec(shape=[1], dtype='float32'),
            paddle.static.InputSpec(shape=[3], dtype='int64'),
        ]
        
    instance_ = None
    static_instance_with_cinn_ = None
    static_instance_without_cinn_ = None


class TestPrimitiveOp_e4a031a743cfbc3e01714ca34f9acf36(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_8a52759e16f03d4d5b0bd5ecb58d0bd7
    def get_inputs(self):
        return [
            paddle.to_tensor([32.0], dtype='float32').reshape([1]),
            paddle.to_tensor([1, 1024, 1], dtype='int64').reshape([3]),
        ]


class TestPrimitiveOp_1fcd1945f02216b5544b0f31f18a31a0(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_8a52759e16f03d4d5b0bd5ecb58d0bd7
    def get_inputs(self):
        return [
            paddle.to_tensor([16.0], dtype='float32').reshape([1]),
            paddle.to_tensor([1, 4096, 1], dtype='int64').reshape([3]),
        ]


class TestPrimitiveOp_18d26c6e185e460881342581223bfaba(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_8a52759e16f03d4d5b0bd5ecb58d0bd7
    def get_inputs(self):
        return [
            paddle.to_tensor([8.0], dtype='float32').reshape([1]),
            paddle.to_tensor([1, 16384, 1], dtype='int64').reshape([3]),
        ]


class TestPrimitiveOp_e4a031a743cfbc3e01714ca34f9acf36(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_8a52759e16f03d4d5b0bd5ecb58d0bd7
    def get_inputs(self):
        return [
            paddle.to_tensor([32.0], dtype='float32').reshape([1]),
            paddle.to_tensor([1, 1024, 1], dtype='int64').reshape([3]),
        ]


class TestPrimitiveOp_1fcd1945f02216b5544b0f31f18a31a0(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_8a52759e16f03d4d5b0bd5ecb58d0bd7
    def get_inputs(self):
        return [
            paddle.to_tensor([16.0], dtype='float32').reshape([1]),
            paddle.to_tensor([1, 4096, 1], dtype='int64').reshape([3]),
        ]


class TestPrimitiveOp_18d26c6e185e460881342581223bfaba(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_8a52759e16f03d4d5b0bd5ecb58d0bd7
    def get_inputs(self):
        return [
            paddle.to_tensor([8.0], dtype='float32').reshape([1]),
            paddle.to_tensor([1, 16384, 1], dtype='int64').reshape([3]),
        ]


class TestPrimitiveOp_18d26c6e185e460881342581223bfaba(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_8a52759e16f03d4d5b0bd5ecb58d0bd7
    def get_inputs(self):
        return [
            paddle.to_tensor([8.0], dtype='float32').reshape([1]),
            paddle.to_tensor([1, 16384, 1], dtype='int64').reshape([3]),
        ]


class TestPrimitiveOp_1fcd1945f02216b5544b0f31f18a31a0(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_8a52759e16f03d4d5b0bd5ecb58d0bd7
    def get_inputs(self):
        return [
            paddle.to_tensor([16.0], dtype='float32').reshape([1]),
            paddle.to_tensor([1, 4096, 1], dtype='int64').reshape([3]),
        ]


class TestPrimitiveOp_e4a031a743cfbc3e01714ca34f9acf36(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_8a52759e16f03d4d5b0bd5ecb58d0bd7
    def get_inputs(self):
        return [
            paddle.to_tensor([32.0], dtype='float32').reshape([1]),
            paddle.to_tensor([1, 1024, 1], dtype='int64').reshape([3]),
        ]


class TestPrimitiveOp_2fdc423b92736d5d6c7f9ea9700ba109(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_8a52759e16f03d4d5b0bd5ecb58d0bd7
    def get_inputs(self):
        return [
            paddle.to_tensor([64.0], dtype='float32').reshape([1]),
            paddle.to_tensor([1, 256, 1], dtype='int64').reshape([3]),
        ]


class TestPrimitiveOp_8b7b4f14998297e64f23e2e8dd0cbcee(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_8a52759e16f03d4d5b0bd5ecb58d0bd7
    def get_inputs(self):
        return [
            paddle.to_tensor([128.0], dtype='float32').reshape([1]),
            paddle.to_tensor([1, 64, 1], dtype='int64').reshape([3]),
        ]


class TestPrimitiveOp_e4a031a743cfbc3e01714ca34f9acf36(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_8a52759e16f03d4d5b0bd5ecb58d0bd7
    def get_inputs(self):
        return [
            paddle.to_tensor([32.0], dtype='float32').reshape([1]),
            paddle.to_tensor([1, 1024, 1], dtype='int64').reshape([3]),
        ]


class TestPrimitiveOp_1fcd1945f02216b5544b0f31f18a31a0(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_8a52759e16f03d4d5b0bd5ecb58d0bd7
    def get_inputs(self):
        return [
            paddle.to_tensor([16.0], dtype='float32').reshape([1]),
            paddle.to_tensor([1, 4096, 1], dtype='int64').reshape([3]),
        ]


class TestPrimitiveOp_18d26c6e185e460881342581223bfaba(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_8a52759e16f03d4d5b0bd5ecb58d0bd7
    def get_inputs(self):
        return [
            paddle.to_tensor([8.0], dtype='float32').reshape([1]),
            paddle.to_tensor([1, 16384, 1], dtype='int64').reshape([3]),
        ]


class TestPrimitiveOp_e4a031a743cfbc3e01714ca34f9acf36(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_8a52759e16f03d4d5b0bd5ecb58d0bd7
    def get_inputs(self):
        return [
            paddle.to_tensor([32.0], dtype='float32').reshape([1]),
            paddle.to_tensor([1, 1024, 1], dtype='int64').reshape([3]),
        ]


class TestPrimitiveOp_1fcd1945f02216b5544b0f31f18a31a0(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_8a52759e16f03d4d5b0bd5ecb58d0bd7
    def get_inputs(self):
        return [
            paddle.to_tensor([16.0], dtype='float32').reshape([1]),
            paddle.to_tensor([1, 4096, 1], dtype='int64').reshape([3]),
        ]


class TestPrimitiveOp_18d26c6e185e460881342581223bfaba(CinnTestBase, unittest.TestCase):
    
    def get_test_class(self):
        return PrimitiveOp_8a52759e16f03d4d5b0bd5ecb58d0bd7
    def get_inputs(self):
        return [
            paddle.to_tensor([8.0], dtype='float32').reshape([1]),
            paddle.to_tensor([1, 16384, 1], dtype='int64').reshape([3]),
        ]




if __name__ == '__main__':
    unittest.main()