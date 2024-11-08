from sklearn.datasets import load_boston
import pandas as pd

# 导入并查看数据
boston_dataset = load_boston()
boston = pd.DataFrame(boston_dataset.data, columns=boston_dataset.feature_names)
boston.head()

# z-score标准化
boston = (boston - boston.mean()) / (boston.std())

# 处理属性名
col_names = boston.columns.values.tolist()
columns = {}
for idx, n in enumerate(col_names):
    columns[n] = "x%d"%idx
boston = boston.rename(columns=columns)

# 插入每行序号和y
boston['y'] = boston_dataset.target
idx = range(boston.shape[0])
boston.insert(0, 'idx', idx)

# 打乱数据生成csv
boston = boston.sample(frac=1)
train = boston.iloc[:406]
eval = boston.iloc[406:]
housing_1_train = train.iloc[:360,:9]
# 再次打乱训练数据
train = train.sample(frac=1)
housing_2_train = train.iloc[:380,[0,9, 10, 11, 12, 13, 14]]
housing_1_eval = eval.iloc[:80,:9]
# 再次打乱测试数据
eval = eval.sample(frac=1)
housing_2_eval = eval.iloc[:85,[0,9, 10, 11, 12, 13, 14]]
housing_1_train.to_csv('housing_1_train.csv', index=False, header=True)
housing_2_train.to_csv('housing_2_train.csv', index=False, header=True)
housing_1_eval.to_csv('housing_1_eval.csv', index=False, header=True)
housing_2_eval.to_csv('housing_2_eval.csv', index=False, header=True)
