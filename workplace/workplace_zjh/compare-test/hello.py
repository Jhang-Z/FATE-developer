import sys
sys.path.append('/data/projects/fate/fate/python/federatedml/secureprotol')
from Compiler.library import *
from Compiler.compilerLib import Compiler
from Compiler.types import *
# hello_world.mpc
from Compiler.library import print_ln
from Compiler.compilerLib import Compiler
hostip='./hostip'
Semi2k_Machine = '/data/projects/fate/fate/python/federatedml/secureprotol/semi2k-party.x'
compiler = Compiler()

@compiler.register_function('helloworld')
def hello_world():
    print_ln('hello world')


compiler.compile_func()

command = [Semi2k_Machine, '-p', 0, '-ip', hostip, '-OF', 'output', 'helloworld']