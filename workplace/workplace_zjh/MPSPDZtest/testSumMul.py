from Compiler.library import print_ln
from Compiler.compilerLib import Compiler
from Compiler.types import *
compiler = Compiler()

@compiler.register_function('testSumMul')
def TEST():
    int_a = sint.get_input_from(0)
    int_b = sint.get_input_from(1)
    

    print_ln('-----------int sum test-----------\n')
    int_sum = int_a + int_b 
   
    print_ln('Results =%s\n',int_sum.reveal())
    print_ln('Results =%s\n',int_sum.reveal())
    print_ln('Results =%s\n',fix_mul.reveal())
    print_ln('-----------int sum test done-----------\n')

    print_ln('-----------int mul test-----------\n')
    int_mul = int_a * int_b 

    print_ln('Results =%s\n',int_mul.reveal())
    print_ln('-----------int mul test done-----------\n')
    
    
    fix_a = sfix.get_input_from(0)
    fix_b = sfix.get_input_from(1)
    print_ln('-----------fix sum test-----------\n')
    fix_sum = fix_a + fix_b 
    print_ln('Results =%s\n',fix_sum.reveal())
    print_ln('-----------fix sum test done-----------\n')

    print_ln('-----------fix mul test-----------\n')
    fix_mul = fix_a * fix_b 

    print_ln('Results =%s\n',fix_mul.reveal())
    print_ln('-----------fix mul test done-----------\n')
    

if __name__ == "__main__":
    
    compiler.compile_func()
    
    
   
        
        
