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

from federatedml.framework.hetero.sync import loss_sync
from federatedml.optim.gradient import hetero_linear_model_gradient
from federatedml.util import LOGGER
from federatedml.util.fate_operator import reduce_add, vec_dot
from federatedml.util import consts

from federatedml.secureprotol.cheetah.fixedpoint_numpy import cheetahFixedPointTensor
import sys
from federatedml.statistic import data_overview
import copy
from federatedml.transfer_variable.transfer_class.batch_generator_transfer_variable import \
    BatchGeneratorTransferVariable
from federatedml.framework.hetero.procedure import paillier_cipher, batch_generator
from federatedml.secureprotol.cheetah.cheetah_fixedpoint import cheetahFixedPointEndec

sys.path.append('/root/pufa/code/fate/standalone_fate_install_1.7.2_release/fate/python/federatedml/opencheetah_notused/OpenCheetah/build/lib')
import libcheetah
variables = []
for i in range(5):
    variables.append((np.random.uniform(1, 10, size=(1,360))).astype(np.uint64))
scal = 5
server_address = "127.0.0.1"
client_address = "127.0.0.1"

server_port = 9370
client_port = 9370

def cheetah_fit(self, data_instance, validate_data=None):
        
        # self.transfer_variable = SSHEModelTransferVariable()
        if self.role == consts.HOST:
            self.batch_generator = batch_generator.Host()
        else:
            self.batch_generator = batch_generator.Guest()
        self.batch_generator.register_batch_generator(BatchGeneratorTransferVariable(), has_arbiter=False)
        self.header = copy.deepcopy(data_instance.schema.get("header", []))
        self._abnormal_detection(data_instance)
        self.check_abnormal_values(data_instance)
        self.check_abnormal_values(validate_data)
        LOGGER.info("data prepared")
        # from cheetah
        model_shape = self.get_features_shape(data_instance)
        LOGGER.debug(f"model_shape: {model_shape}")

        w = self.initializer.init_model(model_shape, init_params=self.init_param_obj)
        w = w.reshape(-1, 1)
        LOGGER.debug(f"w: {w} type(w): {type(w)} w.shape: {w.shape}")

        data_instances_numpy = np.array([i[1] for i in data_instance.collect()])
        features_numpy = np.array([i.features for i in data_instances_numpy])
        if self.role == consts.GUEST:
            features_numpy = np.hstack((features_numpy, np.ones((features_numpy.shape[0], 1))))

            labels_numpy = np.array([i.label for i in data_instances_numpy]).reshape((-1, 1))
        else:
            labels_numpy = None

        # LOGGER.debug(f"data_instances_numpy: {data_instances_numpy}")
        # LOGGER.debug(f"features_numpy: {features_numpy}")
        # LOGGER.debug(f"labels_numpy: {labels_numpy}")

        cheetah_encoded_batch_data = [features_numpy]
        cheetah_batch_labels_list = [labels_numpy]

        while self.n_iter_ < self.max_iter:
            LOGGER.info(f"start to n_iter: {self.n_iter_}")

            LOGGER.debug(f"w: {w} type(w): {type(w)} w.shape: {w.shape}")

            self.optimizer.set_iters(self.n_iter_)
            cheetah_loss_list = []

            for cheetah_batch_idx, cheetah_batch_data in enumerate(cheetah_encoded_batch_data):
                LOGGER.info(
                    f"cheetah_batch_data: {cheetah_batch_data} type(cheetah_batch_data): {type(cheetah_batch_data)} cheetah_batch_data.shape: {cheetah_batch_data.shape}")

                if self.role == consts.GUEST:
                    cheetah_batch_labels = cheetah_batch_labels_list[cheetah_batch_idx]

                else:
                    cheetah_batch_labels = None

                LOGGER.debug(f"cheetah_batch_labels: {cheetah_batch_labels}")

                self.learning_rate = self.optimizer.decay_learning_rate()
                LOGGER.debug(f"self.learning_rate: {self.learning_rate}")
                w = np.random.randint(0, 10, size=(cheetah_batch_data.shape[1], 1), dtype='uint64')
                LOGGER.info("weight shape: {}".format(w.shape))
                LOGGER.info("weight: {}".format(w))
                z = cheetah_batch_data.dot(w)
                # LOGGER.debug(f"z: {z}")
                
                ############################################################################################
                if self.role == consts.HOST:
                     # cheetah开始
                    libcheetah.start(2, self.address, self.port)
                    LOGGER.info("cheetah ing")
        
                    z_host = z
                    LOGGER.debug("cheetah right")
                    # send z_host to guest
                    cheetahFixedPointTensor(
                        cheetahFixedPointEndec.encode(z_host),
                        endec=cheetahFixedPointEndec
                    ).share_add("client")

                    # receive error from guest
                    error = cheetahFixedPointTensor(
                        cheetahFixedPointEndec.encode(self, float_tensor=np.zeros(z_host.shape)),
                        endec=cheetahFixedPointEndec).share_add("client").get()

                    # calculate g_host
                    # todo 有问题
                    g_host = (cheetah_batch_data.T.dot(error) * (1 / error.shape[0]))
                    g_host_without_intercept = g_host[:-1]
                    g_host_without_intercept = g_host_without_intercept + self.alpha * w[:-1]
                    g_host = np.vstack((g_host_without_intercept, g_host[-1]))

                    # update w
                    w = w - self.learning_rate * g_host
                    # cheetah结束
                    libcheetah.end(2)
                    LOGGER.info("Cheetah client ended.")
        
                ####################################################################################
                elif self.role == consts.GUEST:
                    # cheetah开始
                    libcheetah.start(1, self.address, self.port)
                    LOGGER.info("cheetah ing")
                    
                    z_guest = z
                    # receive z_host from host
                    z_host = cheetahFixedPointTensor(
                        cheetahFixedPointEndec.encode(self, float_tensor=np.zeros(z_guest.shape)),
                        endec=cheetahFixedPointEndec).share_add("server")
                    z_host = z_host.get()
                    z_total = z_guest + z_host
                    LOGGER.debug(f"z_total: {z_total} type(z_total): {type(z_total)} z_total.shape: {z_total.shape}")

                    error = z_total - cheetah_batch_labels
                    LOGGER.debug(f"error: {error} type(error): {type(error)} error.shape: {error.shape}")
                    # send error to host
                    cheetahFixedPointTensor(
                        cheetahFixedPointEndec.encode(error),
                        endec=cheetahFixedPointEndec
                    ).share_add("server")

                    loss = (1 / (2 * error.shape[0])) * np.sum(error ** 2)
                    # l2 penalty
                    loss += 0.5 * self.alpha * np.sum(w ** 2)

                    LOGGER.debug(f"loss: {loss} type(loss): {type(loss)}")
                    cheetah_loss_list.append(loss)

                    # calculate g_guest
                    g_guest = (cheetah_batch_data.T.dot(error) * (1 / error.shape[0]))

                    LOGGER.debug(f"g_guest: {g_guest} type(g_guest): {type(g_guest)} g_guest.shape: {g_guest.shape}")

                    g_guest_without_intercept = g_guest[:-1]
                    g_guest_without_intercept = g_guest_without_intercept + self.alpha * w[:-1]
                    g_guest = np.vstack((g_guest_without_intercept, g_guest[-1]))

                    LOGGER.debug(f"g_guest: {g_guest} type(g_guest): {type(g_guest)} g_guest.shape: {g_guest.shape}")
                    # update w
                    w = w - self.learning_rate * g_guest

                    # cheetah结束
                    libcheetah.end(1)
                    LOGGER.info("Cheetah server ended.")
        
            if self.role == consts.GUEST:
                loss = np.sum(cheetah_loss_list) / len(cheetah_loss_list)
                self.cheetah_loss_history.append(loss)
            else:
                loss = None

            self.n_iter_ += 1

        self.model_weights = LinearModelWeights(
            l=w.reshape((-1,)),
            fit_intercept=True if self.role == consts.GUEST else False)

        LOGGER.debug(f"cheetah_loss_history: {self.cheetah_loss_history}")
        self.loss_history = self.cheetah_loss_history
        self.set_summary(self.get_model_summary())
        
def cheetah_matmul_server(matrix, vector, bias, vector_shared=True):
    # 确保matrix是矩阵，vector是向量
    shift = 12
    # LOGGER.info("Server: start computing matmul:{},{},{},{}".format(matrix.shape, vector.shape, bias.shape, resmat.shape))
    matrix = (np.random.rand(360, scal) * 2).astype(np.uint64)
    vector = (np.random.rand(scal, 1) * 2).astype(np.uint64)
    # LOGGER.info("server matmul input size:{},{}".format(matrix.shape, vector.shape))
    
    resmat = np.zeros((matrix.shape[0], vector.shape[1]), dtype=np.uint64)
    # libcheetah.matmul_server(vector.shape[1], matrix.shape[1], matrix.shape[0], vector, matrix, resmat, server_address, server_port)
    resmat = libcheetah.ahe(matrix.shape[0], matrix.shape[1], vector.shape[1], shift, matrix, vector, bias, resmat)
    LOGGER.info("Client: computing matmul ends: {}".format(resmat))
    return resmat

def cheetah_matmul_client(matrix, vector, bias, vector_shared=True):
    # 确保matrix是矩阵，vector是向量
    shift = 12
    # LOGGER.info("client matmul input size:{},{}".format(matrix.shape, vector.shape))
    matrix = (np.random.rand(360, scal) * 2).astype(np.uint64)
    vector = (np.random.rand(scal, 1) * 2).astype(np.uint64)
    
    resmat = np.zeros((matrix.shape[0], vector.shape[1]), dtype=np.uint64)
    # LOGGER.info("Client: start computing matmul:{},{},{},{}".format(matrix.shape, vector.shape, bias.shape, resmat.shape))
    # libcheetah.matmul_client(vector.shape[1], matrix.shape[1], matrix.shape[0], vector, matrix, resmat, client_address, client_port)
    resmat = libcheetah.ahe(matrix.shape[0], matrix.shape[1], vector.shape[1], shift, matrix, vector, bias, resmat)
    LOGGER.info("Client: computing matmul ends: {}".format(resmat))
    return resmat

def cheetah_matadd(matrix1, matrix2):
    if matrix1.shape == matrix2.shape:
        # LOGGER.info("Server: start computing matadd:{},{}".format(matrix1.shape, matrix2.shape))
        resmat = np.zeros(matrix1.shape, dtype=np.uint64)
        resmat = libcheetah.matadd2d(matrix1.shape[0], matrix1.shape[1], matrix1, matrix2, resmat)
    else:
        raise ValueError("matadd存在问题")
    return resmat

def cheetah_matsub(matrix1, matrix2):
    if matrix1.shape == matrix2.shape:
        # LOGGER.info("Server: start computing matadd:{},{}".format(matrix1.shape, matrix2.shape))
        resmat = np.zeros(matrix1.shape, dtype=np.uint64)
        resmat = libcheetah.matsub2d(matrix1.shape[0], matrix1.shape[1], matrix1, matrix2, resmat)
    else:
        raise ValueError("matsub存在问题")
    return resmat

def intermidiate(self, batch_index, batch_data, optim_guest_gradient):
        loss_norm = self.optimizer.loss_norm(self.model_weights)
        self.gradient_loss_operator.compute_loss(batch_data, self.n_iter_, batch_index, loss_norm)
        self.model_weights = self.optimizer.update_model(self.model_weights, optim_guest_gradient)
        
class Guest(hetero_linear_model_gradient.Guest, loss_sync.Guest):

    def register_gradient_procedure(self, transfer_variables):
        self._register_gradient_sync(transfer_variables.host_forward,
                                     transfer_variables.fore_gradient,
                                     transfer_variables.guest_gradient,
                                     transfer_variables.guest_optim_gradient)

        self._register_loss_sync(transfer_variables.host_loss_regular,
                                 transfer_variables.loss,
                                 transfer_variables.loss_intermediate)

    def compute_half_d(self, data_instances, w, cipher, batch_index, current_suffix):
        if self.use_sample_weight:
            self.half_d = data_instances.mapValues(
                lambda v: (vec_dot(v.features, w.coef_) + w.intercept_ - v.label) * v.weight)
        else:
            self.half_d = data_instances.mapValues(
                lambda v: vec_dot(v.features, w.coef_) + w.intercept_ - v.label)
        return self.half_d

    def compute_and_aggregate_forwards(self, data_instances, half_g, encrypted_half_g, batch_index,
                                       current_suffix, offset=None):
        """
        gradient = (1/N)*sum(wx - y) * x
        Define wx -y  as guest_forward and wx as host_forward
        """
        self.host_forwards = self.get_host_forward(suffix=current_suffix)
        return self.host_forwards

    def compute_loss(self, data_instances, n_iter_, batch_index, loss_norm=None):
        '''
        Compute hetero linr loss:
            loss = (1/N)*\sum(wx-y)^2 where y is label, w is model weight and x is features
        log(wx - y)^2 = (wx_h)^2 + (wx_g - y)^2 + 2*(wx_h + wx_g - y)
        '''
        current_suffix = (n_iter_, batch_index)
        n = data_instances.count()
        loss_list = []
        host_wx_squares = self.get_host_loss_intermediate(current_suffix)

        if loss_norm is not None:
            host_loss_regular = self.get_host_loss_regular(suffix=current_suffix)
        else:
            host_loss_regular = []
        if len(self.host_forwards) > 1:
            LOGGER.info("More than one host exist, loss is not available")
        else:
            host_forward = self.host_forwards[0]
            host_wx_square = host_wx_squares[0]

            wxy_square = self.half_d.mapValues(lambda x: np.square(x)).reduce(reduce_add)

            loss_gh = self.half_d.join(host_forward, lambda g, h: g * h).reduce(reduce_add)
            loss = (wxy_square + host_wx_square + 2 * loss_gh) / (2 * n)
            if loss_norm is not None:
                loss = loss + loss_norm + host_loss_regular[0]
            loss_list.append(loss)
        # LOGGER.debug("In compute_loss, loss list are: {}".format(loss_list))
        self.sync_loss_info(loss_list, suffix=current_suffix)

    def compute_forward_hess(self, data_instances, delta_s, host_forwards):
        """
        To compute Hessian matrix, y, s are needed.
        g = (1/N)*∑(wx - y) * x
        y = ∇2^F(w_t)s_t = g' * s = (1/N)*∑(x * s) * x
        define forward_hess = (1/N)*∑(x * s)
        """
        forwards = data_instances.mapValues(
            lambda v: (vec_dot(v.features, delta_s.coef_) + delta_s.intercept_))
        for host_forward in host_forwards:
            forwards = forwards.join(host_forward, lambda g, h: g + h)
        if self.use_sample_weight:
            forwards = forwards.join(data_instances, lambda h, d: h * d.weight)
        hess_vector = self.compute_gradient(data_instances,
                                            forwards,
                                            delta_s.fit_intercept)
        return forwards, np.array(hess_vector)


class Host(hetero_linear_model_gradient.Host, loss_sync.Host):

    def register_gradient_procedure(self, transfer_variables):
        self._register_gradient_sync(transfer_variables.host_forward,
                                     transfer_variables.fore_gradient,
                                     transfer_variables.host_gradient,
                                     transfer_variables.host_optim_gradient)
        self._register_loss_sync(transfer_variables.host_loss_regular,
                                 transfer_variables.loss,
                                 transfer_variables.loss_intermediate)

    def compute_forwards(self, data_instances, model_weights):
        wx = data_instances.mapValues(
            lambda v: vec_dot(v.features, model_weights.coef_) + model_weights.intercept_)
        return wx

    def compute_half_g(self, data_instances, w, cipher, batch_index):
        half_g = data_instances.mapValues(
            lambda v: vec_dot(v.features, w.coef_) + w.intercept_)
        encrypt_half_g = cipher[batch_index].encrypt(half_g)
        return half_g, encrypt_half_g

    def compute_loss(self, model_weights, optimizer, n_iter_, batch_index, cipher_operator):
        '''
        Compute htero linr loss for:
            loss = (1/2N)*\sum(wx-y)^2 where y is label, w is model weight and x is features

            Note: (wx - y)^2 = (wx_h)^2 + (wx_g - y)^2 + 2*(wx_h + (wx_g - y))
        '''

        current_suffix = (n_iter_, batch_index)
        self_wx_square = self.forwards.mapValues(lambda x: np.square(x)).reduce(reduce_add)
        
        en_wx_square = cipher_operator.encrypt(self_wx_square)
        self.remote_loss_intermediate(en_wx_square, suffix=current_suffix)

        loss_regular = optimizer.loss_norm(model_weights)
        if loss_regular is not None:
            en_loss_regular = cipher_operator.encrypt(loss_regular)
            self.remote_loss_regular(en_loss_regular, suffix=current_suffix)


class Arbiter(hetero_linear_model_gradient.Arbiter, loss_sync.Arbiter):
    def register_gradient_procedure(self, transfer_variables):
        self._register_gradient_sync(transfer_variables.guest_gradient,
                                     transfer_variables.host_gradient,
                                     transfer_variables.guest_optim_gradient,
                                     transfer_variables.host_optim_gradient)
        self._register_loss_sync(transfer_variables.loss)

    def compute_loss(self, cipher, n_iter_, batch_index):
        """
        Decrypt loss from guest
        """
        current_suffix = (n_iter_, batch_index)
        loss_list = self.sync_loss_info(suffix=current_suffix)
        de_loss_list = cipher.decrypt_list(loss_list)
        return de_loss_list


