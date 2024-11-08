import sys
sys.path.append('/data/projects/fate/fate/python/federatedml/secureprotol/semi2k')
from Compiler.library import print_ln
from Compiler.compilerLib import Compiler
from Compiler.types import *
from Compiler import ml


from Compiler.library import *

from federatedml.util import LOGGER
import torch
import numpy as np

# 创建一个形状为(3, 4)的二维数组，初始化为零

compiler = Compiler(custom_args=['-R', '64'])

@compiler.register_function('tensor')
def hello_world(): 

    data1 = np.loadtxt('./1000_300_train.csv', delimiter=',', skiprows=1)
    data2 = np.loadtxt('./1100_300_train.csv', delimiter=',', skiprows=1)
    data1 = data1[:, 1:]
    data2 = data2[:, 1:]

    # X_train_guest=sfix.input_tensor_via(1, data1[:,1:],binary=False)
    # Y_train_guest=sfix.input_tensor_via(1,data1[:,0] ,binary=False)
    # X_train_host=sfix.input_tensor_via(0, data2, binary=False)
    
    # print(X_train_guest.shape)
    # print(Y_train_guest.shape)
    # print(X_train_host.shape)
    X_train_guest = sfix.input_tensor_from(1, (569,300))
    s = X_train_guest[2]
    Y_train_guest = sfix.Array(569)
    Y_train_guest.input_from(1)
    
    

    X_train_host=sfix.input_tensor_from(0, (569,20))
                            
    X_train = X_train_guest.concat_columns(X_train_host)
    

    log = ml.SGDLogistic(1, 569, learning_rate = 0.15, tol = 0.0001)
    
    
    
    log.fit(X_train, Y_train_guest)
    # log.opt.reveal_model_to_binary()
    # f = open('Player-Data/Binary-Output-P0-0')
    # for var in log.opt.trainable_variables:
    #     var.write_to_file()
    #     print_ln("%s/n",var.reveal())
        
    # for var in log.opt.trainable_variables:
    #     for a in var:
    #         print_ln("%s\n",a[1].reveal())
    
    
    # model_shape_guest = 10   
    # model_shape_host = 20  
    # w = log.opt.layers[0].W
    # b = log.opt.layers[0].b
    
    # for i in range(model_shape_guest):
    #     print_ln_to(1,"%s\n",w[i].reveal())
        
    # for i in range(model_shape_guest, model_shape_guest +model_shape_host , 1):
    #     print_ln_to(0,"%s\n",w[i].reveal())
        
    # print_ln_to(1,"%s\n",b.reveal())
    


    # start = 0  
    # for var in log.opt.trainable_variables:
    #     start = var.read_from_file(start)
    
    # a = Matrix(1, 4, sfix)
    # b = Matrix(4, 1, sfix)
    
    # a.create_from(sfix.input_tensor_from(0,(4,)))

    #a=sfix.get_input_from(0,size=4)
    
    
    # @for_range_opt(4)
    # def _(i):
        
    #     for j in range(1):
    #         b[i][j] = sfix.get_input_from(0)
    
    # @for_range_opt(1)
    # def _(i):
        
    #     for j in range(4):
    #         a[i][j] = sfix.get_input_from(0)
        

    # M=a *b
    
    # print_ln('a = %s\n', X.reveal()) 
    
    # print_ln('M = %s\n', M.reveal()) 
    
    
    #result=sfix.dot_product(w_host,w_guest)
    
    #print_ln("%s/n",result.reveal())
    
    
    # a = Array(2, sfix)
    # a.read_from_file(0)
    # b = Array(2, sfix)
    # b.read_from_file(1)
    

if __name__ == "__main__":
 
    
    compiler.compile_func()
   