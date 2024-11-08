from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split

X, y = load_breast_cancer(return_X_y=True)

# normalize column-wise
X /= X.max(axis=0)
X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=0)