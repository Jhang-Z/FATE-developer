#!/usr/bin/env python
# -*- coding: utf-8 -*-

from federatedml.transfer_variable.base_transfer_variable import BaseTransferVariables

# noinspection PyAttributeOutsideInit
class VoleIntersectTransferVariable(BaseTransferVariables):
    def __init__(self, flowid=0):
        super().__init__(flowid)
        self.intersect_datasize_guest = self._create_variable(name='intersect_datasize_guest', src=['guest'], dst=['host'])
        self.intersect_datasize_host = self._create_variable(name='intersect_datasize_host', src=['host'], dst=['guest'])
        self.intersect_result = self._create_variable(name='intersect_result', src=['host'], dst=['guest'])