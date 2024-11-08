from Compiler.library import *
from Compiler.compilerLib import Compiler
from Compiler.types import *
import subprocess
compiler = Compiler()

@compiler.register_function('testMatrix')
def TEST():
    data1 = sfix.Matrix(2, 2)
    data2 = sfix.Matrix(2, 2)
    @for_range_opt(2)
    def _(i):
        for j in range(2):
            data1[i][j] = sfix.get_input_from(0)     
                
    @for_range_opt(2)
    def _(i):
        for j in range(2):
            data2[i][j] = sfix.get_input_from(1) 
                
    # 
    print_ln('-----------matrix multiplication test-----------\n')
    M = data1 * data2
    print_ln('%s\t%s\n%s\t%s\n',M[0][0].reveal_to(1),M[0][1].reveal(),M[1][0].reveal(),M[1][1].reveal())


if __name__ == "__main__":
    
    compiler.compile_func()
    
    
   
        
        
