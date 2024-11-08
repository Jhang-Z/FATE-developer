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

from federatedml.statistic.intersect.vole_intersect.vole_intersect_base import VoleIntersect
from fate_arch.session._session import computing_session as session
from fate_arch.abc._computing import CTableABC
from federatedml.util import consts, LOGGER

import numpy as py
import volePSIpy

class VoleIntersectionHost(VoleIntersect):
    def __init__(self):
        super().__init__()
        self.role = consts.HOST

    def run_cache_intersect(self, data_instances, cache_data):
        raise NotImplementedError("method should not be called here")
    
    def run_cardinality(self, data_instances):
        raise NotImplementedError("method should not be called here")

    
    def run_intersect(self, data_instances: CTableABC):
        """
        runs vole intersect
        """

        LOGGER.info("psi start")

        # get table len from CTableABC.count method
        self.setsize = data_instances.count()
        self._sync_setsize_from_guest()
        self._sync_setsize_to_guest()

        # data_key = data_instances.map(lambda k, v: (k, "v"))
        # key_array = self._extract_table_key_to_array(data_key)

        key_array = self._extract_table_key_to_array(data_instances)
        LOGGER.info("key array prepared \n")

        res = volePSIpy.doPSI(key_array, self.setsize, self.host_setsize,
                            role=volePSIpy.Role.Host, seed_str=self.seed_str, stat_sec_param=self.stat_sec_param,
                            ip_addr=self.ip_addr, is_server=self.is_server, threat = self.thread_num, malicious=self.is_malicious,
                            )
        self.res_table = session.parallelize(res, include_key=False, partition=data_instances.partitions)
        self.res_table = self.res_table.map(lambda k, v: (str(v), "intersect_id"))

        # send intersect res to guest
        self._sync_intersect_result_to_guest()
        
        # if value is required, match res_table with data_instances
        if not self.only_output_key:
            # LOGGER.info("data_instances: {}".format(data_instances.take(5)))
            # LOGGER.info("res_table: {}".format(self.res_table.take(5)))
            self.res_table = self.res_table.join(data_instances, lambda v1, v2: v2)
        return self.res_table
    
    def save_data(self):
        return self.res_table
    
    def _sync_setsize_to_guest(self):
        self.transfer_variable.intersect_datasize_host.remote(self.setsize, role="guest", idx=0)
    
    def _sync_setsize_from_guest(self):
        self.host_setsize = self.transfer_variable.intersect_datasize_guest.get(idx=0)
    
    def _sync_intersect_result_to_guest(self):
        self.transfer_variable.intersect_result.remote(self.res_table, role="guest", idx=0)