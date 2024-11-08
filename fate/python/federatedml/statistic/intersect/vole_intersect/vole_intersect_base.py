#
#  Copyright 2021 The FATE Authors. All Rights Reserved.
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

from federatedml.transfer_variable.transfer_class.vole_intersect_transfer_variable import VoleIntersectTransferVariable
from federatedml.param.intersect_param import IntersectParam, VOLEParam
from federatedml.statistic.intersect import Intersect
from federatedml.util import LOGGER
from fate_arch._standalone import Table
import numpy as np

class VoleIntersect(Intersect):
    def __init__(self):
        super().__init__()
        self.role = None
        self.transfer_variable = VoleIntersectTransferVariable()

    def load_params(self, param: IntersectParam):
        super().load_params(param=param)
        self.vole_params: VOLEParam = param.vole_params

        self.salt = self.vole_params.salt
        self.ip_addr = self.vole_params.ip_addr
        self.seed_str = self.vole_params.seed_str
        if self.vole_params.is_server:
            self.is_server = 1
        else:
            self.is_server = 0
        self.thread_num = self.vole_params.threat_num
        self.is_malicious = self.vole_params.is_malicious
        self.stat_sec_param = self.vole_params.stat_sec_param

    def get_intersect_method_meta(self):
        vole_meta = {
            "intersect_method": self.intersect_method,
            "salt": self.salt,
            "ip_addr": self.ip_addr,
            "seed_str": self.seed_str,
            "is_server": self.is_server,
            "thread_num": self.thread_num,
            "is_malicious": self.is_malicious,
            "stat_sec_param": self.stat_sec_param
        }
        return vole_meta

    def _extract_table_key_to_array(self, data: Table) -> np.array:
        size = data.count()
        keys_array = np.empty(size, dtype=np.uint64)
        idx = 0
        for k, _ in data.collect():
            keys_array[idx] = k
            idx += 1
        return keys_array
        # return np.array([k for (k, v) in data.collect()], dtype=np.uint64)