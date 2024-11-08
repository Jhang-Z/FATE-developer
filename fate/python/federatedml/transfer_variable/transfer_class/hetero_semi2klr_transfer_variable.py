#!/usr/bin/env python
# -*- coding: utf-8 -*-
from federatedml.transfer_variable.base_transfer_variable import BaseTransferVariables

# noinspection PyAttributeOutsideInit
class Semi2kLRTransferVariable(BaseTransferVariables):
    def __init__(self, flowid=0):
        super().__init__(flowid)
        self.model_shape_guest = self._create_variable(name='model_shape_guest', src=['guest'], dst=['host'])
        self.model_shape_host = self._create_variable(name='model_shape_host', src=['host'], dst=['guest'])
                                                                                                                      