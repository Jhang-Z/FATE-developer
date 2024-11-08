from Compiler.library import *
from Compiler.compilerLib import Compiler
from Compiler.types import *
import subprocess

Addcompiler = Compiler(custom_args=['-R', '64'])
Mulcompiler = Compiler(custom_args=['-R', '64'])
Martixcompiler = Compiler(custom_args=['-R', '64'])
hostip='/data/projects/fate/fate/python/federatedml/secureprotol/semi2k/hostip'


class Test1():
    def __init__(self,num):
        self.num = num
        with open('./data-P0-0', 'w') as f:
            f.write(str(self.num))
        print("rest")

    def fit(self):
        
        Addcompiler.compile_func()
        # subprocess.run(['./semi2k-party.x', '-p','0','-ip',hostip,'Addtest'])
        subprocess.run(['./semi2k-party.x','-p', '0','-ip',hostip,'-IF','./data','-OF', 'data1', 'Addtest'])
        # subprocess.run(['./semi2k-party.x', '-p','0','Multest'])
        
        
class Test2():
    def __init__(self,num):
        self.num = num
        with open('./data-P1-0', 'w') as f:
            f.write(str(self.num))
            
        

    def fit(self):
        
        Addcompiler.compile_func()
        # subprocess.run(['./semi2k-party.x', '-p','1','-ip',hostip,'Addtest'])
        subprocess.run(['./semi2k-party.x','-p', '1','-ip',hostip,'-IF','./data','-OF', 'data1', 'Addtest'])
        # subprocess.run(['./semi2k-party.x', '-p','1','Multest'])
        
        
        
        
@Addcompiler.register_function('Addtest')
def testrun():
    inta = sint.read_from_file()
    intb = sint.get_input_from(1)
    sum = inta + intb
    print_ln('%s',sum.reveal()) 
          

@Mulcompiler.register_function('Multest')
def testrun():
    inta = sint.get_input_from(0)
    intb = sint.get_input_from(1)
    sum = inta *intb
    print_ln('%s\n',sum.reveal())   

@Martixcompiler.register_function('Martixtest')
def testrun():
    inta = sint.get_input_from(0)
    intb = sint.get_input_from(1)
    sum = inta *intb
    print_ln('%s\n',sum.reveal())  
    
    
# test1=Test1(100)
# test1.fit()


test2=Test2(200)
test2.fit()