import functools
import operator

import numpy as np

from federatedml.ABY.linear_model.bilateral_linear_model.hetero_sshe_linear_model import ABYHeteroSSHEHostBase
from federatedml.param.aby_hetero_sshe_linr_param import ABYHeteroSSHELinRParam
from federatedml.protobuf.generated import linr_model_param_pb2, linr_model_meta_pb2
from federatedml.ABY.aby_secureprotol.spdz.secure_matrix.secure_matrix import SecureMatrix
from federatedml.ABY.aby_secureprotol.spdz.tensor import fixedpoint_numpy
from federatedml.util import consts, fate_operator, LOGGER

from  federatedml.ABY.aby_secureprotol.aby_fixedpoint import ABYFixedPointEndec, ABYFixedPointNumber
from federatedml.ABY.aby_secureprotol.aby.tensor.fixedpoint_numpy import ABYFixedPointTensor

class ABYHeteroLinRHost(ABYHeteroSSHEHostBase):
    def __init__(self):
        super().__init__()
        self.model_name = 'ABYHeteroLinearRegression'
        self.model_param_name = 'ABYHeteroLinearRegressionParam'
        self.model_meta_name = 'ABYHeteroLinearRegressionMeta'
        self.model_param = ABYHeteroSSHELinRParam()
        self.labels = None

    def aby_forward(self, weights, features:ABYFixedPointTensor, labels, suffix, cipher, batch_weight):
        LOGGER.info(f"[aby_forward]: Calculate z host directly...")
        w = weights.unboxed
        w = w.reshape(-1, 1)
        z = features.dot_local(w)   # z_host = x_host * w_host
        LOGGER.debug(f"w: {w}, type(w): {type(w)}, w.shape: {w.shape}")

        LOGGER.debug(f"features: {features}, type(features): {type(features)}, features.shape: {features.shape}")
        LOGGER.debug(f"z: {z}, type(z): {type(z)}, z.shape: {z.shape}")

        self.aby_wx_self = z

        complete_z = z.share_add("client")

        return complete_z





    def forward(self, weights, features, labels, suffix, cipher, batch_weight=None):
        if not self.reveal_every_iter:
            LOGGER.info(f"[forward]: Calculate z in share...")
            w_self, w_remote = weights
            z = self._cal_z_in_share(w_self, w_remote, features, suffix, self.cipher)
        else:
            LOGGER.info(f"[forward]: Calculate z directly...")
            w = weights.unboxed
            z = features.dot_local(w)   # z_host = x_host * w_host

        self.wx_self = z

        self.secure_matrix_obj.share_encrypted_matrix(suffix=suffix,
                                                      is_remote=True,
                                                      cipher=cipher,
                                                      z=z)  # send z_host to guest

        tensor_name = ".".join(("complete_z",) + suffix)
        shared_z = SecureMatrix.from_source(tensor_name,
                                            self.other_party,
                                            cipher,
                                            self.fixedpoint_encoder.n,
                                            self.fixedpoint_encoder)    # receive complete_z = z_guest + z_host = w_guest * x_guest + w_host * x_host = w * x   from guest

        return shared_z

    def aby_compute_loss(self, weights, labels, suffix, cipher):
        LOGGER.info(f"[aby_compute_loss]: Calculate loss ...")

        self.aby_wx_self.share_add("client")

        shared_loss = ABYFixedPointTensor(self.aby_fixedpoint_encoder.encode(np.zeros(shape=self.aby_wx_self.shape)), self.aby_fixedpoint_encoder)
        loss = shared_loss.share_add("client")
        loss = loss.get()
        loss = sum(loss)
        loss_norm = self.optimizer.loss_norm(weights)
        if loss_norm:
            loss += loss_norm

        LOGGER.info(f"[aby_compute_loss]: loss={loss}, reveal_every_iter={self.reveal_every_iter}")

        return loss
        ...

    def compute_loss(self, weights=None, labels=None, suffix=None, cipher=None):
        """
         Compute hetero linr loss:
            loss = (1/N)*\\sum(wx-y)^2 where y is label, w is model weight and x is features
            (wx - y)^2 = (wx_h)^2 + (wx_g - y)^2 + 2 * (wx_h * (wx_g - y))
        """
        LOGGER.info(f"[compute_loss]: Calculate loss ...")
        wx_self_square = (self.wx_self * self.wx_self).reduce(operator.add)

        self.secure_matrix_obj.share_encrypted_matrix(suffix=suffix,
                                                      is_remote=True,
                                                      cipher=cipher,
                                                      wx_self_square=wx_self_square)

        tensor_name = ".".join(("shared_loss",) + suffix)
        share_loss = SecureMatrix.from_source(tensor_name=tensor_name,
                                              source=self.other_party,
                                              cipher=cipher,
                                              q_field=self.fixedpoint_encoder.n,
                                              encoder=self.fixedpoint_encoder,
                                              is_fixedpoint_table=False)


        # LOGGER.debug(f"wx_self_square: {wx_self_square}, wx_self_square_real: {wx_self_square.get()}")

        if self.reveal_every_iter:
            loss_norm = self.optimizer.loss_norm(weights)
            if loss_norm:
                share_loss += loss_norm
            LOGGER.debug(f"share_loss+loss_norm: {share_loss}")
            tensor_name = ".".join(("loss",) + suffix)
            share_loss.broadcast_reconstruct_share(tensor_name=tensor_name)
        else:
            tensor_name = ".".join(("loss",) + suffix)
            share_loss.broadcast_reconstruct_share(tensor_name=tensor_name)
            if self.optimizer.penalty == consts.L2_PENALTY:
                w_self, w_remote = weights

                w_encode = np.hstack((w_self.value, w_remote.value))

                w_encode = np.array([w_encode])

                w_tensor_name = ".".join(("loss_norm_w",) + suffix)
                w_tensor = fixedpoint_numpy.FixedPointTensor(value=w_encode,
                                                             q_field=self.fixedpoint_encoder.n,
                                                             endec=self.fixedpoint_encoder,
                                                             tensor_name=w_tensor_name)

                w_tensor_transpose_name = ".".join(("loss_norm_w_transpose",) + suffix)
                w_tensor_transpose = fixedpoint_numpy.FixedPointTensor(value=w_encode.T,
                                                                       q_field=self.fixedpoint_encoder.n,
                                                                       endec=self.fixedpoint_encoder,
                                                                       tensor_name=w_tensor_transpose_name)

                loss_norm_tensor_name = ".".join(("loss_norm",) + suffix)

                loss_norm = w_tensor.dot(w_tensor_transpose, target_name=loss_norm_tensor_name)
                loss_norm.broadcast_reconstruct_share()

    def predict(self, data_instances):
        LOGGER.info("Start predict ...")
        self._abnormal_detection(data_instances)
        data_instances = self.align_data_header(data_instances, self.header)

        LOGGER.debug(f"Before_predict_reveal_strategy: {self.model_param.reveal_strategy},"
                     f" {self.is_respectively_reveal}")

        def _vec_dot(v, coef, intercept):
            return fate_operator.vec_dot(v.features, coef) + intercept

        f = functools.partial(_vec_dot,
                              coef=self.model_weights.coef_,
                              intercept=self.model_weights.intercept_)
        host_pred = data_instances.mapValues(f)
        self.transfer_variable.host_prob.remote(host_pred, role=consts.GUEST, idx=0)
        LOGGER.info("Remote probability to Guest")

    def _get_param(self):
        if self.need_cv:
            param_protobuf_obj = linr_model_param_pb2.LinRModelParam()
            return param_protobuf_obj

        self.header = self.header if self.header else []
        single_result = self.get_single_model_param()
        param_protobuf_obj = linr_model_param_pb2.LinRModelParam(**single_result)
        return param_protobuf_obj

    def _get_meta(self):
        meta_protobuf_obj = linr_model_meta_pb2.LinRModelMeta(penalty=self.model_param.penalty,
                                                              tol=self.model_param.tol,
                                                              alpha=self.alpha,
                                                              optimizer=self.model_param.optimizer,
                                                              batch_size=self.batch_size,
                                                              learning_rate=self.model_param.learning_rate,
                                                              max_iter=self.max_iter,
                                                              early_stop=self.model_param.early_stop,
                                                              fit_intercept=self.fit_intercept
                                                             )
        return meta_protobuf_obj

    def load_model(self, model_dict):
        result_obj, _ = super().load_model(model_dict)
        self.load_single_model(result_obj)

    def fit(self, data_instances, validate_data=None):
        LOGGER.info("Starting to fit hetero_sshe_linear_regression")
        self.prepare_fit(data_instances, validate_data)

        # self.fit_single_model(data_instances, validate_data)
        self.aby_fit_single_model(data_instances, validate_data)
