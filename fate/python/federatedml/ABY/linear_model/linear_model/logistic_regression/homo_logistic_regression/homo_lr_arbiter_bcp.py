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

import numpy as np
import sys

from federatedml.framework.homo.procedure import aggregator
from federatedml.framework.homo.blocks import bcp_cipher
from federatedml.linear_model.linear_model_weight import LinearModelWeights as LogisticRegressionWeights
from federatedml.linear_model.logistic_regression.homo_logistic_regression.homo_lr_base import HomoLRBase
from federatedml.optim import activation
from federatedml.secureprotol.encrypt import BCPEncrypt
import random

from federatedml.util import LOGGER
from federatedml.util import consts


class HomoLRArbiter(HomoLRBase):
    def __init__(self):
        super(HomoLRArbiter, self).__init__()
        self.re_encrypt_times = []  # Record the times needed for each host

        self.loss_history = []
        self.is_converged = False
        self.role = consts.ARBITER
        # self.aggregator = aggregator.Arbiter()
        self.model_weights = None
        self.cipher = bcp_cipher.Server()
        self.host_predict_results = []
        self.cipher_operator = BCPEncrypt()

    def _init_model(self, params):
        super()._init_model(params)
        

    def fit(self, data_instances=None, validate_data=None):
        
        # self.aggregator = aggregator.Arbiter()
        # self.aggregator.register_aggregator(self.transfer_variable)

        # 不要check了
        # self._server_check_data()
        
        # 与cloudB(host)建立连接
        cipher_withB = bcp_cipher.CloudA()
        
        # 发送公钥
        # host_ciphers = self.cipher.paillier_keygen(key_length=self.model_param.encrypt_param.key_length,
        #                                            suffix=('fit',))
        # host_has_no_cipher_ids = [idx for idx, cipher in host_ciphers.items() if cipher is None]
        
        # ---------接收每个guest公钥-----------
        guest_and_keys = self.cipher.keygen()
        print('guest_and_keys:', type(guest_and_keys), guest_and_keys)
        # -----------------------------------
        
        # 接收 re_encrypt_times
        # self.re_encrypt_times = self.cipher.set_re_cipher_time(host_ciphers)
        
        max_iter = self.max_iter
        # validation_strategy = self.init_validation_strategy()
        
        self.callback_list.on_train_begin(data_instances, validate_data)

        if self.component_properties.is_warm_start:
            self.callback_warm_start_init_iter(self.n_iter_)

        size_send = 0
        size_get = 0
        
        while self.n_iter_ < max_iter + 1:
            suffix = (self.n_iter_,)
            self.callback_list.on_epoch_begin(self.n_iter_)

            if ((self.n_iter_ + 1) % self.aggregate_iters == 0) or self.n_iter_ == max_iter:
                # ------------------------------
                # 接收每个guest模型
                guest_and_models = self.cipher.get_model_list()
                
                size_get_per_niter = sys.getsizeof(guest_and_models)
                print('size_get_per_niter:', size_get_per_niter)
                
                # 加入噪音
                info_dict = {}
                models_to_send = {}
                for guest in guest_and_keys:
                    random_float = random.uniform(0, 20)
                    random_float_rounded = round(random_float, 2)  # 四舍五入到小数点后两位
                    noise = self.cipher_operator.encrypt(guest_and_keys[guest][0], random_float_rounded)
                    model_with_noise = self.cipher_operator.add_list(guest_and_models[guest][0], noise)
                     # 分别为 公钥-int , 模型list [BCPEncryptedNumber], 随机数 float, 噪音 BCPEncryptedNumber, 加噪音的模型 list [BCPEncryptedNumber]
                    info_dict[guest] = (guest_and_keys[guest][0], guest_and_models[guest][0], random_float_rounded, noise, model_with_noise)
                    models_to_send[guest] = model_with_noise
                
                
                # 发送 model_with_noise
                cipher_withB.send_model_with_noise(models_to_send)
                # 接收 aggregated_model_with_noise
                aggregated_model_with_noise = cipher_withB.get_aggregated_model_from_B()
                aggregated_model_with_noise = aggregated_model_with_noise[0]
                
                # 去噪音
                sum_rand = 0
                for guest in info_dict:
                    sum_rand = sum_rand + info_dict[guest][2]
                avg_rand = sum_rand/len(info_dict)
                aggregated_model = {}
                for guest in aggregated_model_with_noise:
                    noise_to_del = self.cipher_operator.encrypt(pk= aggregated_model_with_noise[guest][0].public_key, value= - avg_rand)
                    aggregated_model[guest] =  self.cipher_operator.add_list(values= aggregated_model_with_noise[guest], y= noise_to_del)
                print(aggregated_model)
                
                # 向guest发送
                self.cipher.send_aggregated_model(aggregated_model)
                
                size_send_per_niter = sys.getsizeof(aggregated_model)
                print('size_send_per_niter:', size_send_per_niter)
                size_send = size_send + size_send_per_niter
                size_get = size_get + size_get_per_niter
                # ---------------------------
                
                # # 聚合并广播发送权重
                # merged_model = self.aggregator.aggregate_and_broadcast(ciphers_dict=host_ciphers,
                #                                                        suffix=suffix)
                
                # 收集loss
                total_loss = self.cipher.get_and_cal_loss()
                # total_loss = self.aggregator.aggregate_loss(host_has_no_cipher_ids, suffix)
                
                self.callback_loss(self.n_iter_, total_loss)
                self.loss_history.append(total_loss)
                if self.use_loss:
                    converge_var = total_loss
                else:
                    converge_var = np.array(aggregated_model)

                # 发送收敛状态
                self.is_converged = self.cipher.send_converge_status(self.converge_func.is_converge,
                                                                         (converge_var,))
                # 给CloudB(host)发送
                cipher_withB.send_converged_status(self.is_converged)
                LOGGER.info("n_iters: {}, total_loss: {}, converge flag is :{}".format(self.n_iter_,
                                                                                       total_loss,
                                                                                       self.is_converged))
                print('这里是字典',type(aggregated_model))
                # 取出字典任意一个值即可，发给每方的都一样
                aggregated_model = next(iter(aggregated_model.values()))
                # 适配输出
                fake_weights = np.ones(len(aggregated_model))
                self.model_weights = LogisticRegressionWeights(fake_weights,
                                                               self.model_param.init_param.fit_intercept)
                if self.header is None:
                    self.header = ['x' + str(i) for i in range(len(self.model_weights.coef_))]

                if self.is_converged or self.n_iter_ == max_iter:
                    break
            
            # 重加密
            # self.cipher.re_cipher(iter_num=self.n_iter_,
            #                       re_encrypt_times=self.re_encrypt_times,
            #                       host_ciphers_dict=host_ciphers,
            #                       re_encrypt_batches=self.re_encrypt_batches)

            # validation_strategy.validate(self, self.n_iter_)
            self.callback_list.on_epoch_end(self.n_iter_)
            self.n_iter_ += 1
            if self.stop_training:
                break

        print('-----------size_send---------', size_send)
        print('-----------size_get---------', size_get)
        print('size_all', size_send + size_get)
        
        LOGGER.info("Finish Training task, total iters: {}".format(self.n_iter_))
