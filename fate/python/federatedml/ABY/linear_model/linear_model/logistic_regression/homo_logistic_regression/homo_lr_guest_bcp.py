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

from federatedml.framework.homo.procedure import aggregator
from federatedml.framework.homo.blocks import bcp_cipher
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


class HomoLRGuest(HomoLRBase):
    def __init__(self):
        super(HomoLRGuest, self).__init__()
        
        self.gradient_operator = None
        self.loss_history = []
        self.is_converged = False
        self.role = consts.GUEST
        self.model_weights = None
        self.cipher = None
        
        

    def _init_model(self, params):
        super()._init_model(params)
        self.cipher = bcp_cipher.Client()
        if params.encrypt_param.method in [consts.BCP]:
            self.use_encrypt = True
            # self.gradient_operator = TaylorLogisticGradient()
            self.gradient_operator = LogisticGradient()
            self.re_encrypt_batches = params.re_encrypt_batches
        else:
            self.use_encrypt = False
            self.gradient_operator = LogisticGradient()


    def fit(self, data_instances, validate_data=None):
        # ---------------
        # self.aggregator = aggregator.Guest()
        # self.aggregator.register_aggregator(self.transfer_variable)
        # ---------------

        self._abnormal_detection(data_instances)
        LOGGER.info("这里是check_abnormal前")
        self.check_abnormal_values(data_instances)
        LOGGER.info("这里是check_abnormal后")
        self.init_schema(data_instances)
        LOGGER.info("这里是init_schema后")
        # self._client_check_data(data_instances)
        LOGGER.info("这里是train_begin前")
        self.callback_list.on_train_begin(data_instances, validate_data)
        LOGGER.info("这里是train_begin后，生成公钥前")
        # -----------------
        # 生成bcp加密并发送公钥
        bcp_encrypt = self.cipher.gen_bcp_encrypt_and_send_pk(enable=self.use_encrypt)
        print('bcp_encrypt.public_key', bcp_encrypt.public_key)
        # -----------------
        LOGGER.info("这里是train_begin后，生成公钥后")

        # validation_strategy = self.init_validation_strategy(data_instances, validate_data)
        # 初始化权重
        if not self.component_properties.is_warm_start:
            self.model_weights = self._init_model_variables(data_instances)
        else:
            self.callback_warm_start_init_iter(self.n_iter_)

        max_iter = self.max_iter
        # total_data_num = data_instances.count()
        mini_batch_obj = MiniBatch(data_inst=data_instances, batch_size=self.batch_size)
        model_weights = self.model_weights

        degree = 0
        self.prev_round_weights = copy.deepcopy(model_weights)
        
        size_send = 0
        size_get = 0
        

        while self.n_iter_ < max_iter + 1:
            self.callback_list.on_epoch_begin(self.n_iter_)
            batch_data_generator = mini_batch_obj.mini_batch_data_generator()

            self.optimizer.set_iters(self.n_iter_)
            if ((self.n_iter_ + 1) % self.aggregate_iters == 0) or self.n_iter_ == max_iter:
                
                # -----------
                # 加密
                en_weights = bcp_encrypt.encrypt_list(bcp_encrypt.public_key, model_weights._weights)
                print(en_weights)
                
                # 发送和接收
                size_send_per_niter = sys.getsizeof(en_weights)
                print('size_encrynumber', sys.getsizeof(en_weights[0]))
                print('size_pk', sys.getsizeof(en_weights[0].public_key))
                print('size_ciphertext', sys.getsizeof(en_weights[0].ciphertext))
                print('size_ciphertext[A]', sys.getsizeof(en_weights[0].ciphertext['A']))
                print('size_ciphertext[B]', sys.getsizeof(en_weights[0].ciphertext['B']))
                print('size_exponent', sys.getsizeof(en_weights[0].exponent))
                print('len:', len(en_weights))
                print('size_en_weights', size_send_per_niter)
                
                aggregated_weights = self.cipher.send_then_get_aggregate_model(en_weights)[0]
                
                size_get_per_niter = sys.getsizeof(aggregated_weights)
                print('size_aggregated_weights', size_get_per_niter)
                
                
                # 解密
                aggregated_weights = bcp_encrypt.decrypt_list(bcp_encrypt.privacy_key, aggregated_weights)
                print(aggregated_weights)
                # ------------
                
                # weight = self.aggregator.aggregate_then_get(model_weights, degree=degree,
                #                                             suffix=self.n_iter_)

                self.model_weights = LogisticRegressionWeights(aggregated_weights, self.fit_intercept)

                # store prev_round_weights after aggregation
                self.prev_round_weights = copy.deepcopy(self.model_weights)
                
                # send loss to arbiter
                loss = self._compute_loss(data_instances, self.prev_round_weights)
                self.cipher.send_loss(loss= loss)
                
                print('size_loss', sys.getsizeof(loss))
                size_send_per_niter = size_send_per_niter + sys.getsizeof(loss)
                
                # self.aggregator.send_loss(loss, degree=degree, suffix=(self.n_iter_,))
                degree = 0

                self.is_converged = self.cipher.get_converge_status()
                # self.is_converged = self.aggregator.get_converge_status(suffix=(self.n_iter_,))
                LOGGER.info("n_iters: {}, loss: {} converge flag is :{}".format(self.n_iter_, loss, self.is_converged))
                
                print('size_send_per_niter:', size_send_per_niter)
                print('size_get_per_niter:', size_get_per_niter)
                size_send = size_send + size_send_per_niter
                size_get = size_get + size_get_per_niter
                
                print('self.n_iter_', self.n_iter_)
                if self.is_converged or self.n_iter_ == max_iter:
                    break
                model_weights = self.model_weights

            batch_num = 0
            for batch_data in batch_data_generator:
                n = batch_data.count()
                # LOGGER.debug("In each batch, lr_weight: {}, batch_data count: {}".format(model_weights.unboxed, n))
                f = functools.partial(self.gradient_operator.compute_gradient,
                                      coef=model_weights.coef_,
                                      intercept=model_weights.intercept_,
                                      fit_intercept=self.fit_intercept)
                grad = batch_data.applyPartitions(f).reduce(fate_operator.reduce_add)
                grad /= n
                # LOGGER.debug('iter: {}, batch_index: {}, grad: {}, n: {}'.format(
                #     self.n_iter_, batch_num, grad, n))

                if self.use_proximal:  # use proximal term
                    model_weights = self.optimizer.update_model(model_weights, grad=grad,
                                                                has_applied=False,
                                                                prev_round_weights=self.prev_round_weights)
                else:
                    model_weights = self.optimizer.update_model(model_weights, grad=grad,
                                                                has_applied=False)

                batch_num += 1
                degree += n

            # validation_strategy.validate(self, self.n_iter_)
            self.callback_list.on_epoch_end(self.n_iter_)
            self.n_iter_ += 1

            if self.stop_training:
                break
        
        print('-----------size_send---------', size_send)
        print('-----------size_get---------', size_get)
        print('size_all', size_send + size_get)
        
        self.set_summary(self.get_model_summary())

    @assert_io_num_rows_equal
    def predict(self, data_instances):

        self._abnormal_detection(data_instances)
        self.init_schema(data_instances)

        data_instances = self.align_data_header(data_instances, self.header)
        # predict_wx = self.compute_wx(data_instances, self.model_weights.coef_, self.model_weights.intercept_)
        pred_prob = data_instances.mapValues(lambda v: activation.sigmoid(vec_dot(v.features, self.model_weights.coef_)
                                                                          + self.model_weights.intercept_))

        predict_result = self.predict_score_to_output(data_instances, pred_prob, classes=[0, 1],
                                                      threshold=self.model_param.predict_param.threshold)

        return predict_result
