#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

import copy
import functools
import sys

from federatedml.framework.homo.blocks import bcp_cipher
from federatedml.secureprotol.encrypt import BCPEncrypt
from federatedml.linear_model.linear_model_weight import LinearModelWeights as LogisticRegressionWeights
from federatedml.linear_model.logistic_regression.homo_logistic_regression.homo_lr_base import HomoLRBase
from federatedml.model_selection import MiniBatch
from federatedml.feature.instance import Instance
from federatedml.optim import activation
from federatedml.util.fate_operator import vec_dot
from federatedml.optim.gradient.homo_lr_gradient import LogisticGradient, TaylorLogisticGradient
from federatedml.protobuf.generated import lr_model_param_pb2
from federatedml.util import LOGGER
from federatedml.util import consts
from federatedml.util import fate_operator
from federatedml.util.io_check import assert_io_num_rows_equal


class HomoLRHost(HomoLRBase):
    def __init__(self):
        super(HomoLRHost, self).__init__()
        self.gradient_operator = None
        self.loss_history = []
        self.is_converged = False
        self.role = consts.HOST
        # self.aggregator = aggregator.Host()
        self.model_weights = None
        self.cipher = None

    def _init_model(self, params):
        super()._init_model(params)
        if self.component_properties.has_arbiter:
            self.cipher = bcp_cipher.CloudB()
        if params.encrypt_param.method in [consts.BCP]:
            self.cipher_operator = BCPEncrypt()
            self.use_encrypt = True
            self.gradient_operator = TaylorLogisticGradient()
            self.re_encrypt_batches = params.re_encrypt_batches
        else:
            self.use_encrypt = False
            self.gradient_operator = LogisticGradient()

    def fit(self, data_instances=None, validate_data=None):
        
        # 获取主密钥
        mk = self.cipher_operator.mk
        
        self.model_weights = self._init_model_variables(data_instances)
        self.callback_list.on_train_begin(data_instances, validate_data)
        
        if self.component_properties.is_warm_start:
            self.callback_warm_start_init_iter(self.n_iter_)
        
        size_send = 0
        size_get = 0
        
        while self.n_iter_ < self.max_iter + 1:
            self.callback_list.on_epoch_begin(self.n_iter_)

            if ((self.n_iter_ + 1) % self.aggregate_iters == 0) or self.n_iter_ == self.max_iter:
                
                # 接收 model_with_noise   
                guest_and_models = self.cipher.get_model_with_noise()
                
                size_get_per_niter = sys.getsizeof(guest_and_models)
                print('size_get_per_niter', size_get_per_niter)
                
                # 去除传输产生的一层[]
                guest_and_models = guest_and_models[0]
                # 解密
                models_decrypted = {}
                for guest in guest_and_models:
                    models_decrypted[guest] = self.cipher_operator.decryptMK_list(mk, guest_and_models[guest])
                print(models_decrypted)
                # 聚合
                avg_num = len(models_decrypted)
                sumed_values = [sum(x) for x in zip(*models_decrypted.values())]
                aggregated_model = [x / avg_num for x in sumed_values]
                print(aggregated_model)
                # 加密
                for guest in guest_and_models:
                    guest_and_models[guest] = self.cipher_operator.encrypt_list(guest_and_models[guest][0].public_key, aggregated_model)
                print(guest_and_models)
                # 发送
                self.cipher.send_aggregated_model_to_A(guest_and_models)
                
                size_send_per_niter = sys.getsizeof(guest_and_models)
                print('size_send_per_niter', size_send_per_niter)
                size_get = size_get + size_get_per_niter
                size_send = size_send + size_send_per_niter
                
                
                # 获取当前迭代是否已收敛的状态
                self.is_converged = self.cipher.get_converge_status()
                LOGGER.info("n_iters: {}, is_converge: {}".format(self.n_iter_, self.is_converged))
                if self.is_converged or self.n_iter_ == self.max_iter:
                    break
                

            # validation_strategy.validate(self, self.n_iter_)
            self.callback_list.on_epoch_end(self.n_iter_)
            self.n_iter_ += 1
            if self.stop_training:
                break

        print('-----------size_send---------', size_send)
        print('-----------size_get---------', size_get)
        print('size_all', size_send + size_get)

        LOGGER.info("Finish Training task, total iters: {}".format(self.n_iter_))

