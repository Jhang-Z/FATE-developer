import sys
sys.path.append('/data/projects/fate/fate/python/federatedml/secureprotol')
from Compiler.library import *
from Compiler.compilerLib import Compiler
from Compiler.types import *
import subprocess
from Compiler import ml
from federatedml.util import LOGGER
import numpy as np

hostip = '/data/projects/fate/workplace_zjh/compare-test/hostip'
Semi2k_Machine = '/data/projects/fate/fate/python/federatedml/secureprotol/semi2k-party.x'
get_SGDLogistic_compiler= Compiler(custom_args=['-R', '64'])
get_data_compiler = Compiler(custom_args=['-R', '64'])

instances_count = 5000
model_shape_guest = 300
 
model_shape_host = 300

LOGGER.info("get_data start")

@get_data_compiler.register_function('get_data')
def get_data():

    sfix.input_tensor_via(1, features_array1, binary=False)
    sfix.input_tensor_via(1, label_array, binary=False)
    # sfix.input_tensor_via(0, features_array0, binary=False)

        
    

@get_SGDLogistic_compiler.register_function('SGDLogistic')
def SGDLogistic():

    X_train_guest=sfix.input_tensor_from(1, (instances_count,model_shape_guest))
            
    Y_train_guest=sfix.Array(instances_count)
    Y_train_guest.input_from(1)
        
    X_train_host=sfix.input_tensor_from(0, (instances_count,model_shape_host))
                            
    X_train = X_train_guest.concat_columns(X_train_host)
            
    # print_ln("%s",X_train[3].reveal())
    # print_ln("%s",Y_train_guest[3].reveal())
           
    log = ml.SGDLogistic(20, 5000)

    #log.fit(X_train, Y_train_guest)
    log.fit(X_train, Y_train_guest)
    w = log.opt.layers[0].W 
    b = log.opt.layers[0].b
            
    for i in range(model_shape_guest):
        print_ln_to(1,"%s\n",w[i].reveal())
        
    for i in range(model_shape_guest, model_shape_guest + model_shape_host , 1):
        print_ln_to(0,"%s\n",w[i].reveal())
        
    print_ln_to(20,"%s\n",b.reveal())




features_array1 = np.random.rand(5000, 300)
features_array0 = np.random.rand(5000, 300)

label_array = np.random.randint(0, 2, size=(5000, 1))

LOGGER.info("get_data start")

get_data_compiler.compile_func()  


LOGGER.info("get_data end")

LOGGER.info("get_SGDLogistic_ start")
    
get_SGDLogistic_compiler.compile_func()

LOGGER.info("get_SGDLogistic_ end")

                        
# command = [Semi2k_Machine, '-p', '1', '-ip', hostip, '-OF', 'output', 'SGDLogistic']
command = [Semi2k_Machine, '-p', '1', '-OF', 'output', 'SGDLogistic']


process = subprocess.Popen(command)
process.wait()


if process.returncode == 0:
    LOGGER.info("Command executed successfully.")
else:
    LOGGER.info("Command execution failed.")
process.wait()

LOGGER.info("SGDLogistic over")
        
