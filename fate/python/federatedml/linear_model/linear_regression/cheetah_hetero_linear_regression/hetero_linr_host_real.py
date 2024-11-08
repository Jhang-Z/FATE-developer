#
#  Copyright 2019 The FATE Authors. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

from federatedml.framework.hetero.procedure import convergence
from federatedml.framework.hetero.procedure import paillier_cipher, batch_generator
from federatedml.linear_model.linear_model_weight import LinearModelWeights
from federatedml.linear_model.linear_regression.hetero_linear_regression.hetero_linr_base import HeteroLinRBase
from federatedml.optim.gradient import hetero_linr_gradient_and_loss
from federatedml.secureprotol import EncryptModeCalculator
from federatedml.util import LOGGER
from federatedml.util import consts

from federatedml.optim.gradient.cheetah_hetero_linr_gradient_and_loss import cheetah_matmul_client,cheetah_matadd,cheetah_matsub

import numpy as np
import sys
sys.path.append('/root/pufa/code/fate/standalone_fate_install_1.7.2_release/fate/python/federatedml/opencheetah/OpenCheetah/build/lib')
import libcheetah

class HeteroLinRHost(HeteroLinRBase):
    def __init__(self):
        super(HeteroLinRHost, self).__init__()
        self.batch_num = None
        self.batch_index_list = []
        self.role = consts.HOST

        self.cipher = paillier_cipher.Host()
        self.batch_generator = batch_generator.Host()
        self.gradient_loss_operator = hetero_linr_gradient_and_loss.Host()
        self.converge_procedure = convergence.Host()
        self.encrypted_calculator = None
        self.address = "127.0.0.1"
        self.port = 12345

    def fit(self, data_instances, validate_data=None):
        """
        Train linear regression model of role host
        Parameters
        ----------
        data_instances: Table of Instance, input data
        """

        LOGGER.info("Enter hetero_linR host")
        self._abnormal_detection(data_instances)
        self.header = self.get_header(data_instances)
        self.callback_list.on_train_begin(data_instances, validate_data)

        self.cipher_operator = self.cipher.gen_paillier_cipher_operator()

        if self.transfer_variable.use_async.get(idx=0):
            LOGGER.debug(f"set_use_async")
            self.gradient_loss_operator.set_use_async()

        self.batch_generator.initialize_batch_generator(data_instances)
        self.gradient_loss_operator.set_total_batch_nums(self.batch_generator.batch_nums)

        self.encrypted_calculator = [EncryptModeCalculator(self.cipher_operator,
                                                           self.encrypted_mode_calculator_param.mode,
                                                           self.encrypted_mode_calculator_param.re_encrypted_rate) for _
                                     in range(self.batch_generator.batch_nums)]

        LOGGER.info("Start initialize model.")
        model_shape = self.get_features_shape(data_instances)
        if self.init_param_obj.fit_intercept:
            self.init_param_obj.fit_intercept = False

        if not self.component_properties.is_warm_start:
            w = self.initializer.init_model(model_shape, init_params=self.init_param_obj)
            self.model_weights = LinearModelWeights(w, fit_intercept=self.fit_intercept, raise_overflow_error=False)
        else:
            self.callback_warm_start_init_iter(self.n_iter_)

        # cheetah开始
        libcheetah.start(2, self.address, self.port)
        LOGGER.info("Cheetah started.")
        
        while self.n_iter_ < self.max_iter:
            self.callback_list.on_epoch_begin(self.n_iter_)
            LOGGER.info("iter:" + str(self.n_iter_))
            self.optimizer.set_iters(self.n_iter_)
            batch_data_generator = self.batch_generator.generate_batch_data()
            batch_index = 0
            for batch_data in batch_data_generator:

                # 计算gradient
                current_suffix = (self.n_iter_, batch_index)

                # 计算forwards: WX + b
                # self.forwards = self.compute_forwards(data_instances, self.model_weights)
                # LOGGER.info("self.model_weights.intercept_!!!!!!!!: {}".format(self.model_weights.intercept_))

                bias = np.zeros([360,1], dtype=np.float64)
                mat_in = (np.random.rand(360, 8) * 2).astype(np.uint64)
                mat_in2 = (np.random.rand(8, 1) * 2).astype(np.uint64)
                cheetah_matmul_client(mat_in, mat_in2, bias, True)
                LOGGER.info("small_func done: WX is computed!!!!!!!!!!")

                # grad
                mat_in = (np.random.rand(1, 360) * 2).astype(np.uint64)
                mat_in2 = (np.random.rand(1, 360) * 2).astype(np.uint64)
                gradient = cheetah_matsub(mat_in, mat_in2)
                LOGGER.info("unilateral_gradient is computed!!!!!!!!!!")
                
                # 计算loss
                loss = 0
                wx_h = (np.random.rand(1, 360) * 2).astype(np.uint64)
                wx_g = (np.random.rand(1, 360) * 2).astype(np.uint64)
                y = (np.random.rand(1, 360) * 2).astype(np.uint64)
                for i in range(180):
                    temp = cheetah_matsub(wx_g, y)
                    loss += (1/2*360)*cheetah_matadd(cheetah_matadd(np.square(wx_h), np.square(temp)), 2*(cheetah_matadd(wx_h, cheetah_matsub(wx_g, y))))
                    LOGGER.info("LOSS!:{}".format(i))   
                LOGGER.info("LOSS is finished")   
                
                model_weights = cheetah_matsub(wx_h, gradient)
                batch_index += 1
                
            LOGGER.info("Get is_converged flag from arbiter:{}".format(self.is_converged))
            self.callback_list.on_epoch_end(self.n_iter_)
            self.n_iter_ += 1
            if self.stop_training:
                break

            LOGGER.info("iter: {}, is_converged: {}".format(self.n_iter_, self.is_converged))
            if self.is_converged:
                break
            
        LOGGER.info("iter break out")
        self.callback_list.on_train_end()

        # self.set_summary(self.get_model_summary())
        LOGGER.info("summary out")
        # LOGGER.debug(f"summary content is: {self.summary()}")
        # cheetah结束
        libcheetah.end(2)
        LOGGER.info("Cheetah client ended.")
        

    def predict(self, data_instances):
        """
        Prediction of linR
        Parameters
        ----------
        data_instances:Table of Instance, input data
        """
        
        self.transfer_variable.host_partial_prediction.disable_auto_clean()

        LOGGER.info("Start predict ...")

        self._abnormal_detection(data_instances)
        data_instances = self.align_data_header(data_instances, self.header)

        pred_host = self.compute_wx(data_instances, self.model_weights.coef_, self.model_weights.intercept_)
        self.transfer_variable.host_partial_prediction.remote(pred_host, role=consts.GUEST, idx=0)
        LOGGER.info("Remote partial prediction to Guest")