# -*- coding: utf-8 -*-
import pandas as pd

# # 读取CSV文件
df = pd.read_csv('/data/projects/fate/workplace_lyl/hetero_sshe_linr_test/data/lr_test.csv')

# 打乱所有行
df = df.sample(frac=1).reset_index(drop=True)

# 将打乱后的DataFrame保存回CSV文件
# df.to_csv('shuffled_file.csv', index=False)

# import pandas as pd

# # 读取CSV文件
# df = pd.read_csv('/data/projects/fate/workplace_lyl/hetero_sshe_linr_test/data/shuffled_file.csv')

# 为DataFrame添加一个新的列，包含从0开始的增序整数
#df['new_column'] = range(len(df))

# 如果你想替换第一列而不是添加一个新列，可以使用以下代码：
# df.iloc[:, 0] = range(len(df))

# # 将修改后的DataFrame保存回CSV文件
# # 如果你添加了新列，确保在保存时不包含原来的索引列
# df.to_csv('modified_file.csv', index=False)



import pandas as pd

# 读取CSV文件
df = pd.read_csv('modified_file.csv')

# 计算要删除的列的索引
# 假设CSV文件至少有8列，否则这里需要做异常处理
columns_to_drop = df.columns[10:14]

# 删除后8列
df.drop(columns=columns_to_drop, inplace=True)

# 将修改后的DataFrame保存回CSV文件
df.to_csv('lr_test1.csv', index=False)