import pandas as pd
import numpy as np
import os


data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
print(data_path)


X1 = np.arange(2001, 2011).reshape(10, 1)
X2 = np.arange(1001, 1011).reshape(10, 1)
X3 = np.arange(1, 11).reshape(10, 1)
Y = X1 + 2 * X2 + 3 * X3 + 4


data = np.hstack((Y, X1, X2, X3))

data.astype(np.int32)

data = pd.DataFrame(data, columns=['y', 'x1', 'x2', 'x3'])


data.insert(0, 'id', range(0, 0 + len(data)))


data_guest = data[['id', 'y', 'x1']]

data_host = data[['id', 'x2', 'x3']]

data_guest.to_csv(os.path.join(data_path, "hetero_sshe_linr_test_guest.csv"), index=False)
data_host.to_csv(os.path.join(data_path, "hetero_sshe_linr_test_host.csv"), index=False)

