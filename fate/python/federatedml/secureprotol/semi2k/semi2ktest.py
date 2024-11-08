from federatedml.model_base import ModelBase
from federatedml.util import LOGGER
from federatedml.param.semi2ktest_param import Semi2kTestParam
from Compiler.library import print_ln
from Compiler.compilerLib import Compiler
from Compiler.types import *

import os

import subprocess


SintAddcompiler = Compiler(custom_args=['-R', '64'])
SintMulcompiler = Compiler(custom_args=['-R', '64'])
SfixAddcompiler = Compiler(custom_args=['-R', '64'])
SfixMulcompiler = Compiler(custom_args=['-R', '64'])
Semi2k_Machine = '/data/projects/fate/My_test/semi2ktest/semi2k-party.x'
hostip='/data/projects/fate/fate/python/federatedml/secureprotol/semi2k/hostip'

class Semi2kTest(ModelBase):
    def __init__(self):
        super().__init__()
    def SintAdd(self, num= None, PartyId = None):
        inputpath= './data-P'+PartyId+'-0'
        with open(inputpath, 'w') as f:
            f.write(str(num))
        SintAddcompiler.compile_func()
        result=subprocess.run([Semi2k_Machine,'-p', PartyId,'-ip',hostip,'-IF','./data','-OF', 'output', 'sintadd']) 
        outputpath = './output-P'+PartyId+'-0'
        with open(outputpath , 'r') as f:
            content = f.read()
        role = "Host" if PartyId =="0" else "Guest"
        LOGGER.info(role+" Sum Result:"+str(content))
        
        
    def SintMul(self, new_file_path, num= None, PartyId = None):
        with open(new_file_path, 'w') as f:
            f.write(str(num))
        SintMulcompiler.compile_func()
        subprocess.run([Semi2k_Machine,'-p', PartyId,'-ip',hostip,'-OF', 'Intput', 'sintmul'])
        
        
    def SfixAdd(self, new_file_path, num= None, PartyId = None):
        with open(new_file_path, 'w') as f:
            f.write(str(num))
        SfixAddcompiler.compile_func()
        subprocess.run([Semi2k_Machine,'-p', PartyId,'-ip',hostip,'-OF', 'Intput', 'sfixadd'])
        
    def SfixMul(self, new_file_path, num= None, PartyId = None):
        with open(new_file_path, 'w') as f:
            f.write(str(num))
        SfixMulcompiler.compile_func()
        subprocess.run([Semi2k_Machine,'-p', PartyId,'-ip',hostip,'-OF', 'Intput', 'sfixmul'])
        
        


class Semi2kTestHost(Semi2kTest):
    def __init__(self):
        super().__init__()
        self.model_name = 'Semi2kTestHost'
        self.model_param = Semi2kTestParam()
        # self.new_folder_path = './Player-Data/'
        # self.new_file_name = 'Input-P0-0'
        # self.new_file_path = os.path.join(self.new_folder_path, self.new_file_name)
        # os.makedirs(self.new_folder_path, exist_ok=True)
        
        

    def fit(self,dafalut=0):
        """
        测试
        """
        LOGGER.info("Start Semi2k Prob Test Host")
        num = 6
        LOGGER.info("Host input:"+str(num))
        super().SintAdd(num, "0")
        # super().SintMul(self.new_file_path, 6, "0")
        # super().SfixAdd(self.new_file_path, 4.5, "0")
        # super().SfixMul(self.new_file_path, 4.5, "0")
        # with open("./output-P0-0", 'r') as f:
        #     content = f.read()
        # LOGGER.info("Host Result:"+str(content))
        
        
class Semi2kTestGuest(Semi2kTest):
    def __init__(self):
        super().__init__()
        self.model_name = 'Semi2kTestGuest'
        self.model_param = Semi2kTestParam()
        # self.new_folder_path = './Player-Data/'
        # self.new_file_name = 'Input-P1-0'
        # self.new_file_path = os.path.join(self.new_folder_path, self.new_file_name)
        # os.makedirs(self.new_folder_path, exist_ok=True)

    def fit(self,dafalut=0):
        """
        测试
        """
        LOGGER.info("Start Semi2k Prob Test Guest")
        num = 12
        LOGGER.info("Guest input:"+str(num))
        super().SintAdd(num, "1")
        # super().SintMul(self.new_file_path, 6, "0")
        # super().SfixAdd(self.new_file_path, 4.5, "0")
        # super().SfixMul(self.new_file_path, 4.5, "0")  
        # with open("./output-P1-0", 'r') as f:
        #     content = f.read()
        # LOGGER.info("Guest Result:"+str(content))      
        
        
        

@SintAddcompiler.register_function('sintadd')
def SintAddRun():
    sint_0 = sint.get_input_from(0)
    sint_1 = sint.get_input_from(1)
    result = sint_0 + sint_1
    print_ln('%s',result.reveal())
       

@SintMulcompiler.register_function('sintmul')
def SintMulRun():
    sint_0 = sint.get_input_from(0)
    sint_1 = sint.get_input_from(1)
    result = sint_0 * sint_1
    print_ln('%s',result.reveal())
 

@SfixAddcompiler.register_function('sfixadd')
def SfixAddRun():
    sfix_0 = sint.get_input_from(0)
    sfix_1 = sint.get_input_from(1)
    result = sfix_0 + sfix_1
    print_ln('%s',result.reveal())
   

@SfixMulcompiler.register_function('sfixmul')
def SfixMulRun():
    sfix_0 = sint.get_input_from(0)
    sfix_1 = sint.get_input_from(1)
    result = sfix_0 * sfix_1
    print_ln('%s',result.reveal())
    
    
    
