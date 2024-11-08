import abc

from federatedml.secureprotol.spdz.utils import NamingService


class TensorBase(object):
    __array_ufunc__ = None

    def __init__(self, R_ring, tensor_name: str = None):
        self.R_ring = R_ring
        self.tensor_name = NamingService.get_instance().next() if tensor_name is None else tensor_name

    @classmethod
    def get_semi2k(cls):
        from federatedml.secureprotol.semi2k import SEMI2K
        return SEMI2K.get_instance()

    @abc.abstractmethod
    def dot(self, other, target_name=None):
        pass
    
    
    
    
