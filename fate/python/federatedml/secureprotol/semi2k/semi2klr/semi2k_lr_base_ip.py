import copy
from abc import ABC

import numpy as np

from fate_arch.session import get_parties
from federatedml.framework.hetero.procedure import batch_generator
from federatedml.linear_model.linear_model_base import BaseLinearModel
from federatedml.linear_model.linear_model_weight import LinearModelWeights
from federatedml.one_vs_rest.one_vs_rest import one_vs_rest_factory
from federatedml.param.semi2klr_param import Semi2kLogisticRegressionParam
from federatedml.param.logistic_regression_param import InitParam
from federatedml.protobuf.generated import lr_model_meta_pb2
from federatedml.secureprotol import EncryptModeCalculator
from federatedml.secureprotol import PaillierEncrypt
from federatedml.secureprotol.fixedpoint import FixedPointEndec
from federatedml.secureprotol.spdz import SPDZ
from federatedml.secureprotol.spdz.secure_matrix.secure_matrix import SecureMatrix
from federatedml.secureprotol.spdz.tensor import fixedpoint_numpy, fixedpoint_table
from federatedml.transfer_variable.transfer_class.batch_generator_transfer_variable import \
    BatchGeneratorTransferVariable
from federatedml.transfer_variable.transfer_class.converge_checker_transfer_variable import \
    ConvergeCheckerTransferVariable
from federatedml.transfer_variable.transfer_class.sshe_model_transfer_variable import SSHEModelTransferVariable
from federatedml.util import LOGGER
from federatedml.util import consts
import os
import sys
sys.path.append('/data/projects/fate/fate/python/federatedml/secureprotol/semi2k')
from Compiler.library import *
from Compiler.compilerLib import Compiler
from Compiler.types import *
import subprocess
from Compiler import ml

import typing

from fate_arch.abc import CTableABC
from fate_arch.common import log
from fate_arch.common.profile import computing_profile
from fate_arch.computing._type import ComputingEngine
from fate_arch.common.address import PathAddress

get_data_compiler = Compiler(custom_args=['-R', '64'])
get_SGDLogistic_compiler= Compiler(custom_args=['-R', '64'])

hostip="./hostip"

Semi2k_Machine = '/data/projects/fate/fate/python/federatedml/secureprotol/semi2k/semi2k-party.x'   
 
    
class Semi2kLRBase(BaseLinearModel, ABC):
    def __init__(self):
        LOGGER.info("__init__ begin")
        super().__init__()
        self.model_name = 'Semi2k-HeteroSSHELogisticRegression'
        self.model_param_name = 'Semi2k-HeteroSSHELogisticRegressionParam'
        self.model_meta_name = 'Semi2k-HeteroSSHELogisticRegressionMeta'
        self.mode = consts.HETERO
        self.cipher = None
        self.q_field = None
        self.model_param = Semi2kLogisticRegressionParam()
        self.labels = None
        self.batch_num = []
        self.one_vs_rest_obj = None
        self.secure_matrix_obj: SecureMatrix
        self._set_parties()
        self.cipher_tool = None
        self.host_address_port = None
        self.guest_address_port = None
        
        
    def _transfer_q_field(self):
        LOGGER.info("_transfer_q_field begin")
        if self.role == consts.GUEST:
            q_field = self.cipher.public_key.n
            self.transfer_variable.q_field.remote(q_field, role=consts.HOST, suffix=("q_field",))

        else:
            q_field = self.transfer_variable.q_field.get(role=consts.GUEST, idx=0,
                                                          suffix=("q_field",))

        return q_field

    def _init_model(self, params: Semi2kLogisticRegressionParam):
        LOGGER.info("_init_model begin")
        LOGGER.info("params"+str(params.init_param.init_method))
        super()._init_model(params)
        self.encrypted_mode_calculator_param = params.encrypted_mode_calculator_param
        LOGGER.info("init_param_obj.init_method:"+str(self.init_param_obj.init_method))
        if self.role == consts.HOST:
            self.init_param_obj.fit_intercept = False
        
        LOGGER.info("init_param_obj.init_method:"+str(self.init_param_obj.init_method))
        self.cipher = PaillierEncrypt()
        self.cipher.generate_key(self.model_param.encrypt_param.key_length)
        self.transfer_variable = SSHEModelTransferVariable()
        self.one_vs_rest_obj = one_vs_rest_factory(self, role=self.role, mode=self.mode, has_arbiter=False)

        self.converge_func_name = params.early_stop
        self.reveal_every_iter = params.reveal_every_iter

        self.q_field = self._transfer_q_field()

        LOGGER.debug(f"q_field: {self.q_field}")

        if not self.reveal_every_iter:
            self.self_optimizer = copy.deepcopy(self.optimizer)
            self.remote_optimizer = copy.deepcopy(self.optimizer)

        self.batch_generator = batch_generator.Guest() if self.role == consts.GUEST else batch_generator.Host()
        self.batch_generator.register_batch_generator(BatchGeneratorTransferVariable(), has_arbiter=False)
        self.fixedpoint_encoder = FixedPointEndec(n=self.q_field)
        self.converge_transfer_variable = ConvergeCheckerTransferVariable()
        self.secure_matrix_obj = SecureMatrix(party=self.local_party,
                                              q_field=self.q_field,
                                              other_party=self.other_party)

    def _init_weights(self, model_shape):
        LOGGER.info("_init_weights begin")
        LOGGER.info("init_params:"+str(self.init_param_obj.init_method))
        return self.initializer.init_model(model_shape, init_params=self.init_param_obj)

    def _set_parties(self):
        LOGGER.info("_set_parties begin")
        parties = []
        guest_parties = get_parties().roles_to_parties(["guest"])
        host_parties = get_parties().roles_to_parties(["host"])
        parties.extend(guest_parties)
        parties.extend(host_parties)

        local_party = get_parties().local_party
        other_party = parties[0] if parties[0] != local_party else parties[1]

        self.parties = parties
        self.local_party = local_party
        self.other_party = other_party
        
    def fit(self, data_instances, validate_data=None):
        self.header = data_instances.schema.get("header", [])
        model_shape = self.get_features_shape(data_instances)
        instances_count = data_instances.count()
        
        tuples_list=data_instances.collect()
        features_array = np.zeros((instances_count, model_shape))
        label_array = np.zeros((instances_count, 1))  
        
        if self.role == consts.GUEST:
            for i, item in enumerate(tuples_list):
                features_array[i] = item[1].features
                label_array[i] = item[1].label
                
        else:  
            for i, item in enumerate(tuples_list):
                features_array[i] = item[1].features
            
        if self.role == consts.GUEST:
             LOGGER.info("label[1]:" + str(label_array[3]))
        LOGGER.info("feature.shape:" + str(features_array.shape))
        LOGGER.info("label_array.shape:" + str(label_array.shape))
        LOGGER.info("feature[1]:" + str(features_array[3]))
        
        self.get_ip()

        
        @get_data_compiler.register_function('get_data')
        def get_data():
            if self.local_party.role == consts.GUEST:
                sfix.input_tensor_via(1, features_array, binary=False)
                sfix.input_tensor_via(1, label_array, binary=False)
                
            else:
                sfix.input_tensor_via(0, features_array, binary=False)
        
        get_data_compiler.compile_func()  
        
        
        model_shape_guest = 10
        model_shape_host = 20
        
        @get_SGDLogistic_compiler.register_function('SGDLogistic')
        def SGDLogistic():

            X_train_guest=sfix.input_tensor_from(1, (instances_count,model_shape_guest))
            
            Y_train_guest=sfix.Array(instances_count)
            Y_train_guest.input_from(1)
            
            X_train_host=sfix.input_tensor_from(0, (instances_count,model_shape_host))
                            
            X_train = X_train_guest.concat_columns(X_train_host)
            
            # print_ln("%s",X_train[3].reveal())
            # print_ln("%s",Y_train_guest[3].reveal())
           
            log = ml.SGDLogistic(1, self.batch_size, learning_rate = self.model_param.learning_rate, tol = self.model_param.tol)

            #log.fit(X_train, Y_train_guest)
            log.fit(X_train, Y_train_guest)
            w = log.opt.layers[0].W 
            b = log.opt.layers[0].b
            
            for i in range(model_shape_guest):
                print_ln_to(1,"%s\n",w[i].reveal())
        
            for i in range(model_shape_guest, model_shape_guest + model_shape_host , 1):
                print_ln_to(0,"%s\n",w[i].reveal())
        
            print_ln_to(1,"%s\n",b.reveal())
    
        get_SGDLogistic_compiler.compile_func()
                        
        command = [Semi2k_Machine, '-p', self.PartyID, '-ip', hostip, '-OF', 'output', 'SGDLogistic']
        
        process = subprocess.Popen(command)
        process.wait()
     
        file_path ="./output-P"+self.PartyID+"-0"
        
        current_path = os.getcwd()
        LOGGER.info("Current Path:"+str(current_path))
        
        W = np.loadtxt(file_path)
      
        
        
    #     with open(file_path, 'r') as file:
    #         content = file.read()

    # # Split the content by lines
    #     lines = content.strip().split('\n')
    
    # # Prepare an empty list to store all the numbers
    #     all_numbers = []
    
    # # Process each line
    #     for line in lines:
    #         if line.strip():  # Only process non-empty lines
    #         # Extract numbers from the current line
    #             numbers = re.findall(r"[-\d.]+", line)
    #         # Convert extracted strings to floats and extend the main list
    #             all_numbers.extend(map(float, numbers))
    
    # # Convert the list to a numpy array
    #     data = np.array(all_numbers)
        
    #     if self.role == consts.GUEST:
    #         W = data[0:model_shape]
    #         b = data[-1]
    #     else:
    #         W = data[-model_shape-1:-1]
            
    #     if self.fit_intercept:
    #         if isinstance(model_shape, int):
    #             W = np.append(W, b)
        #---------------------------------------------------------------------------    
        # with open(file_path, 'r') as file:
        #     lines = file.readlines()  
            
        # for line in lines:
        #     LOGGER.info(line)
        # LOGGER.info("subprocess result:"+str(process))
        LOGGER.info("w:"+str(W))
        
        self.model_weights = LinearModelWeights(l=W,
                                                    fit_intercept=self.model_param.init_param.fit_intercept)
        LOGGER.info("self.model_weights:"+str(self.model_weights))
        self.set_summary(self.get_model_summary())
        
        # if self.role == consts.GUEST:
        #     loss = np.sum(loss_list) / instances_count
        #     self.loss_history.append(loss)
        #     if self.need_call_back_loss:
        #         self.callback_loss(self.n_iter_, loss)
        #     else:
        #         loss = None
        
        
    
    def get_model_summary(self):
        LOGGER.info("get_model_summary")
        header = self.header
        if header is None:
            return {}
        weight_dict, intercept_ = self.get_weight_intercept_dict(header)
        best_iteration = -1 if self.validation_strategy is None else self.validation_strategy.best_iteration
        
        
        summary = {"coef": weight_dict,
                   "intercept": intercept_,
                   "is_converged": self.is_converged,
                   "one_vs_rest": self.need_one_vs_rest,
                   "best_iteration": best_iteration}

        if not self.is_respectively_reveal:
            del summary["intercept"]
            del summary["coef"]

        if self.validation_strategy:
            validation_summary = self.validation_strategy.summary()
            if validation_summary:
                summary["validation_metrics"] = validation_summary
                
        return summary
       
    def _get_meta(self):
        LOGGER.info("base:_get_meta")
        meta_protobuf_obj = lr_model_meta_pb2.LRModelMeta(penalty=self.model_param.penalty,
                                                          tol=self.model_param.tol,
                                                          alpha=self.alpha,
                                                          optimizer=self.model_param.optimizer,
                                                          batch_size=self.batch_size,
                                                          learning_rate=self.model_param.learning_rate,
                                                          max_iter=self.max_iter,
                                                          early_stop=self.model_param.early_stop,
                                                          fit_intercept=self.fit_intercept,
                                                          need_one_vs_rest=self.need_one_vs_rest,
                                                          reveal_strategy=self.model_param.reveal_strategy)
        return meta_protobuf_obj
            
        
    def get_single_model_param(self, model_weights=None, header=None):
        LOGGER.info("base:get_single_model_param")
      
        LOGGER.info("self.model_weights._weights:"+str(self.model_weights))
        LOGGER.info("self.model_weights.intercept_:"+str(self.model_weights.intercept_))
        
        header = header if header else self.header
        result = {'iters': self.n_iter_,
                  'loss_history': self.loss_history,
                  'is_converged': self.is_converged,
                  # 'weight': weight_dict,
                  'intercept': self.model_weights.intercept_,
                  'header': header,
                  'best_iteration': -1 if self.validation_strategy is None else
                  self.validation_strategy.best_iteration
                  }

        if self.role == consts.GUEST or self.is_respectively_reveal:
            
            LOGGER.info("model_weights:"+str(model_weights))
            LOGGER.info("self.model_weights:"+str(self.model_weights))
            
            model_weights = model_weights if model_weights else self.model_weights
            weight_dict = {}
            for idx, header_name in enumerate(header):
                coef_i = model_weights.coef_[idx]
                weight_dict[header_name] = coef_i
                LOGGER.info("coef_i:"+str(model_weights.coef_[idx]))
            result['weight'] = weight_dict
            LOGGER.info("self.model_weights:"+str(self.model_weights))

        return result

    @property
    def is_respectively_reveal(self):
        return self.model_param.reveal_strategy == "respectively"
    
    def get_ip(self):
        with open(hostip, "w") as file:
            file.write(self.model_param.guest_address_port)
            file.write(self.model_param.host_address_port)
        
        # return 
        # LOGGER.info("fit begin")
        # self.header = data_instances.schema.get("header", [])
        # LOGGER.info("self.header:"+str(self.header))
        # LOGGER.info("data_instances:"+str(data_instances))
        
        # self._abnormal_detection(data_instances)
        # self.check_abnormal_values(data_instances)
        # self.check_abnormal_values(validate_data)
        # classes = self.one_vs_rest_obj.get_data_classes(data_instances)

        # if len(classes) > 2:
        #     self.need_one_vs_rest = True
        #     self.need_call_back_loss = False
        #     self.one_vs_rest_fit(train_data=data_instances, validate_data=validate_data)
        # else:
        #     self.need_one_vs_rest = False
        #     self.fit_binary(data_instances, validate_data)
           
        
    # def fit_binary(self, data_instances, validate_data=None):
    #     LOGGER.info("Starting to hetero_sshe_logistic_regression")
    #     self.callback_list.on_train_begin(data_instances, validate_data)

    #     model_shape = self.get_features_shape(data_instances)
        

        # LOGGER.info("model_shape:"+str(model_shape))
        # instances_count = data_instances.count()
        # LOGGER.info("instances_count:"+str(instances_count))

        # if not self.component_properties.is_warm_start:
        #     w = self._init_weights(model_shape)
        #     LOGGER.info("w type:"+str(type(w)))
        #     LOGGER.info("w:"+str(w))
        #     self.model_weights = LinearModelWeights(l=w,
        #                                             fit_intercept=self.model_param.init_param.fit_intercept)
            
        #     LOGGER.info("self.model_weights :"+str(self.model_weights ))
        #     last_models = copy.deepcopy(self.model_weights)
        # else:
        #     last_models = copy.deepcopy(self.model_weights)
        #     w = last_models.unboxed
        #     self.callback_warm_start_init_iter(self.n_iter_)
        
    
        # @get_w_compiler.register_function('get_w')
        # def get_w_host():
        #     if self.local_party.role == consts.GUEST:
        #         sfix.input_tensor_via(1, w, binary=False)
                
        #     else:
        #         sfix.input_tensor_via(0, w, binary=False)
            
        # get_w_compiler.compile_func()  

        
         
        


                