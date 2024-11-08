from Compiler.library import print_ln
from Compiler.compilerLib import Compiler
from Compiler.types import *
from Compiler import ml


compiler = Compiler(custom_args=['-R', '64'])

@compiler.register_function('tensor')
def hello_world(): 
    debug = False
    tensor0 = sfix.input_tensor_from(0,(6,))
    tensor1 = sfix.input_tensor_from(1,(6,))
    program.options_from_args()
    print_ln('b =%s\n',str(program.options_from_args()))
    
    sfix.write_to_file(tensor0)
    sfix.write_to_file(tensor1)
    
    a=Array.create_from(sfix.read_from_file(0, 2)[1])
    b=Array.create_from(sfix.read_from_file(2, 2)[1])
    
    # a = Array(2, sfix)
    # a.read_from_file(0)
    # b = Array(2, sfix)
    # b.read_from_file(1)
    
    result=sfix.dot_product(a,b)
    print_ln('a =%s\n',a.reveal())
    print_ln('b =%s\n',b.reveal())
    # print_ln('c =%s\n',c.reveal())
    print_ln('result =%s\n',result.reveal())
    
    
    # sfix(1244).reveal().store_in_mem(0)
    # sfix(122).reveal().store_in_mem(1)
    
    
    
    # a=sfix.load_mem(0)
    # b=sfix.load_mem(1)
    # c=a+b

    # sfix.write_to_file(result)
    # a=sfix.Tensor((1,))
    # a.read_from_file(0)
    # b=sfix.Tensor((1,))
    # b.read_from_file(1)
    # c=a+b
    # print_ln('c=%s\n',c.reveal())

    #
   



if __name__ == "__main__":
    
    compiler.compile_func()
   