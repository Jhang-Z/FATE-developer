from Compiler.library import print_ln
from Compiler.compilerLib import Compiler
from Compiler.types import *
from Compiler import ml

from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split



compiler = Compiler(custom_args=['-R', '128',])

@compiler.register_function('lr')
def logisitic(): 
    from sklearn.datasets import load_breast_cancer
    from sklearn.model_selection import train_test_split

    X, y = load_breast_cancer(return_X_y=True)

    # normalize column-wise
    X /= X.max(axis=0)
    X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=0)

    
    # split by sample
     # split by sample
    a = sfix.input_tensor_via(0, X_train[len(X_train) // 2:])
    b = sfix.input_tensor_via(1, X_train[:len(X_train) // 2])
    X_train = a.concat(b)

    a = sint.input_tensor_via(0, y_train[len(y_train) // 2:])
    b = sint.input_tensor_via(1, y_train[:len(y_train) // 2])
    y_train = a.concat(b)


  
    X_test = sfix.input_tensor_via(0, X_test)
    y_test = sint.input_tensor_via(0, y_test)

    from Compiler import ml

    log = ml.SGDLogistic(20, 2)

    log.fit(X_train, y_train)
    print_ln('%s', (log.predict(X_test) - y_test.get_vector()).reveal())

    # log.fit_with_testing(X_train, y_train, X_test, y_test)
    # print_ln('%s', (log.predict_proba(X_test) - y_test.get_vector()).reveal())





if __name__ == "__main__":
    
    compiler.compile_func()