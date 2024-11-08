import sys
sys.path.append('/data/projects/fate/fate/python/federatedml/secureprotol')
from Compiler.library import print_ln
from Compiler.compilerLib import Compiler
from Compiler.types import *
from Compiler import ml


from Compiler.library import *

from federatedml.util import LOGGER
import torch
import numpy as np


compiler = Compiler(custom_args=['-R', '64'])


# @get_data_compiler.register_function('get_data')
# def get_data():
#     if self.local_party.role == consts.GUEST:
#         sfix.input_tensor_via(1, features_array, binary=False)
#         sfix.input_tensor_via(1, label_array, binary=False)
                
#     else:
#         sfix.input_tensor_via(0, features_array, binary=False)
        
    # get_data_compiler.compile_func()  





@compiler.register_function('tensor')
def hello_world(): 

    data1 = np.loadtxt('./1000_300_train.csv', delimiter=',', skiprows=1)
    data2 = np.loadtxt('./1100_300_train.csv', delimiter=',', skiprows=1)
    data1 = data1[1:1000, 1:]
    data2 = data2[1:1000, 1:]
    X_train_guest=sfix.input_tensor_via(1, data1[:,1:])
    Y_train_guest=sfix.input_tensor_via(1,data1[:,0])
    X_train_host=sfix.input_tensor_via(0, data2)

    X_train = X_train_guest.concat_columns(X_train_host)


    log = ml.SGDLogistic(3, 999, learning_rate = 0.15, tol = 0.0001)
    
    log.fit(X_train, Y_train_guest)
    # w = log.opt.layers[0].W 
    # b = log.opt.layers[0].b
            
    # for i in range(model_shape_guest):
    #             print_ln_to(1,"%s\n",w[i].reveal())
        
    # for i in range(model_shape_guest, model_shape_guest + model_shape_host , 1):
    #         print_ln_to(0,"%s\n",w[i].reveal())
        
    # print_ln_to(1,"%s\n",b.reveal())


if __name__ == "__main__":
 
    
    compiler.compile_func()