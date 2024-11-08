from typing import Union

# from fate.python.federatedml.util.consts import ARBITER, GUEST, HOST
from federatedml.util.consts import ARBITER, GUEST, HOST
from federatedml.framework.homo.blocks.base import HomoTransferBase
from federatedml.secureprotol.encrypt import BCPEncrypt
from federatedml.framework.homo.blocks import has_converged, loss_scatter, model_scatter, model_broadcaster
from federatedml.framework.homo.blocks import random_padding_cipher
from federatedml.framework.homo.blocks.base import HomoTransferBase
from federatedml.framework.homo.blocks.has_converged import HasConvergedTransVar
from federatedml.framework.homo.blocks.loss_scatter import LossScatterTransVar
from federatedml.framework.homo.blocks.model_broadcaster import ModelBroadcasterTransVar
from federatedml.framework.homo.blocks.model_scatter import ModelScatterTransVar
from federatedml.framework.homo.blocks.random_padding_cipher import RandomPaddingCipherTransVar
from federatedml.framework.weights import Weights, NumericWeights, TransferableWeights
from federatedml.transfer_variable.base_transfer_variable import BaseTransferVariables
from federatedml.util import LOGGER
from federatedml.util import consts
import types
from charm.core.math.integer import integer



class BCPCipherTransVar_CloudB(HomoTransferBase):
    def __init__(self, server=(consts.HOST, ), clients=(consts.ARBITER, ), prefix=None):
        super().__init__(server=server, clients=clients, prefix=prefix)
        self.public_param_to_A = self.create_server_to_client_variable(name="public_param_to_A")
        self.client_model_from_A = self.create_client_to_server_variable(name="client_model_from_A")
        self.aggregated_model_from_B = self.create_server_to_client_variable(name="aggregated_model_from_B")
        self.has_converged_from_A = self.create_client_to_server_variable(name="has_converged_from_A")
        
# class BCPCipherTransVar_MKTOB(HomoTransferBase):
#     def __init__(self, server=(consts.HOST, ), clients=(consts.GUEST,), prefix=None):
#         super().__init__(server=server, clients=clients, prefix=prefix)
#         self.mk_from_guest = self.create_client_to_server_variable(name="mk_from_guest")

class BCPCipherTransVar(HomoTransferBase):
    def __init__(self, server=(consts.ARBITER,), clients=(consts.GUEST,), prefix=None):
        super().__init__(server=server, clients=clients, prefix=prefix)
        self.public_param_from_A = self.create_server_to_client_variable(name="public_param_from_A")
        self.use_encrypt = self.create_client_to_server_variable(name="use_encrypt")
        self.bcp_pubkey = self.create_client_to_server_variable(name="bcp_pubkey")
        self.client_model = self.create_client_to_server_variable(name="client_model")
        self.aggregated_model = self.create_server_to_client_variable(name="aggregated_model")
        self.loss = self.create_client_to_server_variable(name="loss")
        self.aggregated_loss = self.create_server_to_client_variable(name="aggregated_loss")
        self.has_converged = self.create_server_to_client_variable(name="has_converged")
        
        
        # self.model_to_aggregate = self.create_client_to_server_variable(name="model_to_aggregate")
        
        
        # self.re_encrypt_times = self.create_client_to_server_variable(name="re_encrypt_times")
        # self.model_to_re_encrypt = self.create_client_to_server_variable(name="model_to_re_encrypt")
        # self.model_re_encrypted = self.create_server_to_client_variable(name="model_re_encrypted")

class CloudA(object):
    
    def __init__(self, trans_var: BCPCipherTransVar_CloudB = None):
        if trans_var is None:
            trans_var = BCPCipherTransVar_CloudB()
        self._public_param_to_A = trans_var.public_param_to_A
        self._client_model_from_A = trans_var.client_model_from_A
        self._aggregated_model_from_B = trans_var.aggregated_model_from_B
        self._has_converged_from_A = trans_var.has_converged_from_A
        
        self._server_parties = trans_var.server_parties
    
    def get_public_param(self):
        param = self._public_param_to_A.get_parties(parties= self._server_parties)
        return param
        
    def send_model_with_noise(self, model_with_noise):
        
        self._client_model_from_A.remote_parties(obj= model_with_noise, parties= self._server_parties)
        
    def get_aggregated_model_from_B(self):
        
        aggregated_model = self._aggregated_model_from_B.get_parties(parties= self._server_parties)
        
        return aggregated_model
    
    def send_converged_status(self, is_converge):
        
        self._has_converged_from_A.remote_parties(obj= is_converge, parties= self._server_parties)
    
class CloudB(object):
    
    def __init__(self, trans_var: BCPCipherTransVar_CloudB = None):
        if trans_var is None:
            trans_var = BCPCipherTransVar_CloudB()
        self._public_param_to_A = trans_var.public_param_to_A
        self._client_model_from_A = trans_var.client_model_from_A
        self._aggregated_model_from_B = trans_var.aggregated_model_from_B
        self._has_converged_from_A = trans_var.has_converged_from_A
        
        self._client_parties = trans_var.client_parties
        
        # special_trans_var = BCPCipherTransVar_MKTOB()
        # self._mk_from_guest = special_trans_var.mk_from_guest
        # self._guests = special_trans_var.client_parties
        
       
    # def get_MK(self):
    #     mk = self._mk_from_guest.get_parties(parties= self._guests) 
    #     return mk
     
    def send_public_param(self, param):
        self._public_param_to_A.remote_parties(obj= param, parties= self._client_parties)
        
    def get_model_with_noise(self):
        
        model_with_noise = self._client_model_from_A.get_parties(parties= self._client_parties)
        
        return model_with_noise
    
    def send_aggregated_model_to_A(self, aggregated_model):
        
        self._aggregated_model_from_B.remote_parties(obj= aggregated_model, parties= self._client_parties)

    def get_converge_status(self):
        
        is_converge = self._has_converged_from_A.get_parties(parties=self._client_parties)
        
        return is_converge[0]
    
class Server(object):

    def __init__(self, trans_var: BCPCipherTransVar = None):
        if trans_var is None:
            trans_var = BCPCipherTransVar()
        self._public_param_from_A = trans_var.public_param_from_A
        self._use_encrypt = trans_var.use_encrypt
        self._bcp_pubkey = trans_var.bcp_pubkey
        self._client_model = trans_var.client_model
        self._aggregated_model = trans_var.aggregated_model
        self._loss = trans_var.loss
        self._aggregated_loss = trans_var.aggregated_loss
        self._has_converged = trans_var.has_converged
        
        # self._re_encrypt_times = trans_var.re_encrypt_times
        # self._model_to_re_encrypt = trans_var.model_to_re_encrypt
        # self._model_re_encrypted = trans_var.model_re_encrypted

        self._client_parties = trans_var.client_parties

    def send_public_param(self, param):
        self._public_param_from_A.remote_parties(obj= param, parties= self._client_parties)
    
    def keygen(self) -> dict:
        # 对于使用加密的client(guest),获取每个公钥(多密钥加密),返回字典
        use_cipher = self._use_encrypt.get_parties(parties=self._client_parties)
        
        guest_and_keys = dict()
        for party in self._client_parties:
            guest_and_keys[party] = self._bcp_pubkey.get_parties(parties=[party])
                
        return guest_and_keys

    def get_model_list(self) -> dict:
        
        guest_and_models = dict()
        for party in self._client_parties:
            guest_and_models[party] = self._client_model.get_parties(parties=[party])
    
        return guest_and_models

    def send_aggregated_model(self, aggregated_model):
        
        for party in aggregated_model:
            self._aggregated_model.remote_parties(obj= aggregated_model[party], parties=[party])
   
    def get_and_cal_loss(self):
        
        loss_list = self._loss.get_parties(parties=self._client_parties)
        if len(loss_list) == 1:
            loss_list = loss_list[0]
        loss_sum = 0
        for loss in loss_list:
            loss_sum = loss_sum + loss
        aggregated_loss = loss_sum / len(loss_list)
        return aggregated_loss
    
    # 应该不用发
    def send_aggregated_loss(self, aggregated_loss):
        
        self._aggregated_loss.remote_parties(obj= aggregated_loss, parties= self._client_parties)
    
    def send_converge_status(self, converge_func: types.FunctionType, converge_args):
        is_converge = converge_func(*converge_args)
        self._has_converged.remote_parties(obj=is_converge, parties= self._client_parties)
        return is_converge
        
        
    
class Client(object):

    def __init__(self, trans_var: BCPCipherTransVar = None):
        if trans_var is None:
            trans_var = BCPCipherTransVar()
        self._public_param_from_A = trans_var.public_param_from_A
        self._use_encrypt = trans_var.use_encrypt
        self._bcp_pubkey = trans_var.bcp_pubkey
        self._client_model = trans_var.client_model
        self._aggregated_model = trans_var.aggregated_model
        self._loss = trans_var.loss
        self._aggregated_loss = trans_var.aggregated_loss
        self._has_converged = trans_var.has_converged
        # self._re_encrypt_times = trans_var.re_encrypt_times
        # self._model_to_re_encrypt = trans_var.model_to_re_encrypt
        # self._model_re_encrypted = trans_var.model_re_encrypted

        self._server_parties = trans_var.server_parties
        
        # special_trans_var = BCPCipherTransVar_MKTOB()
        # self._mk_from_guest = special_trans_var.mk_from_guest
        # self._cloudB = special_trans_var.server_parties

    def get_public_param(self):
        param = self._public_param_from_A.get_parties(parties= self._server_parties)
        return param
    
    def gen_bcp_encrypt_and_send_pk(self, enable, param) -> BCPEncrypt :
        
        self._use_encrypt.remote_parties(obj=enable, parties=self._server_parties)
        if enable:
            
            cipher = BCPEncrypt(param= param)
            public_key, privacy_key = cipher.generate_key()
            self._bcp_pubkey.remote_parties(obj=int(public_key), parties=self._server_parties)
            
            return cipher
        return None

    def send_then_get_aggregate_model(self, model):
        # 发送
        self._client_model.remote_parties(obj= model, parties= self._server_parties)
        # 接收
        aggregated_model = self._aggregated_model.get_parties(parties= self._server_parties)
        
        return aggregated_model
    
    def send_loss(self, loss):
        
        self._loss.remote_parties(obj= loss, parties= self._server_parties)

    # 暂时不接收
    def get_aggregated_loss(self):
        
        aggregated_loss = self._aggregated_loss.get_parties(parties= self._server_parties)
        
        return aggregated_loss
    
    def get_converge_status(self):
        is_converge = self._has_converged.get_parties(parties=self._server_parties)
        return is_converge[0]