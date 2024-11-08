import functools
import numpy as np
from fate_arch.common import Party
from fate_arch.computing import is_table
from federatedml.secureprotol.semi2k.tensor.base import TensorBase
from federatedml.util import LOGGER

from Compiler.library import *
from Compiler.compilerLib import Compiler
from Compiler.types import *
import subprocess

Dotcompiler = Compiler(custom_args=['-R', '64'])

class Semi2kFixedPointTensor(TensorBase):
    __array_ufunc__ = None

    def __init__(self, R_ring, value, tensor_name: str = None):
        super().__init__(R_ring, tensor_name)
        self.value = value
    
    @property
    def shape(self):
        return self.value.shape
    
    
    def reshape(self, shape):
        return self._boxed(self.value.reshape(shape))
    
    
    def dot():
        # 实现点积
        sfix.get_input_from()
        
    @classmethod
    def from_source(cls, tensor_name, source, **kwargs):
        #从数据源获取数据并拆分为秘密共享的Semi2kFixedPointTensor类型分别给两个参与方
        sfix.get_input_from
        
        pass
    
    
    def reconstruct(self, tensor_name=None, broadcast=True):
        # 重构秘密】
        pass
    
    
    def __add__(self, other):
        # 实现加法    
        
        pass
        return self.__boxed()
    
    
    
    
    def __sub__(self, other):
        # 实现减法
        pass
    
    def __mul__(self, other):
        # 实现乘法
        pass
    
    
    def __matmul__(self. other):
        pass
    
    
    def _boxed(self, value, tensor_name=None):
        # 返回了一个参数实例
        return Semi2kFixedPointTensor(value=value, , tensor_name=tensor_name)
    
    
    
            
            
            
    
@Dotcompiler.register_function('tensordot')
def dot_product():
    sfix_0=sfix.Tensor(0)
    sfix_1=sfix.Tensor(1)
    Result=sfix.dot_product(sfix_0, sfix_1)
    print_ln('%s\n',Result.reveal())  
    
    


value1 = np .array([1,2,3,4])
value2 = np .array([2,2,2,2])

Test=FixedPointTensor(4,100,123,"value")  
print(Test.dot(value2,"value2") )
 
    
    

